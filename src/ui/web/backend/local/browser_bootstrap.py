"""
Browser Bootstrap — Node.js binary download and Playwright Chromium install.

Downloads Node.js and Playwright's Chromium browser in background on startup
so the browser automation modules work in packaged (PyInstaller) mode.

First-run-download model (Chromium is NOT bundled into the build): both the
Node.js driver runtime (~30 MB) and the Chromium browser (~150 MB) are fetched
the first time the app runs. This module makes that download *reliable* and
*surfaced*:

- A module-level provisioning status machine (``get_provisioning_status()``)
  that the health endpoint / UI can read. States: pending → provisioning →
  ready | degraded. On failure the status carries a precise, user-facing
  reason instead of being silently swallowed as a log warning.
- Bounded retry with backoff, and idempotent / resumable downloads (a
  half-written node dir or chromium-* dir is cleaned before re-install).
- ``provision_browser_engine()`` can be called again at any time to retry
  (e.g. a user who was offline at first launch), without reinstalling the app.
- Progress is emitted through the standard ``logger`` — which is wired to the
  ``/ws/logs`` WebSocket the frontend already consumes — and mirrored into the
  status object's ``progress`` field. No new channel is invented.
- The crawl entry point can call ``browser_engine_error()`` to get a precise
  user-facing message ("Browser engine not installed — ...; retry") when the
  engine is missing, instead of a generic ImportError / launch timeout.
"""
import asyncio
import logging
import os
import shutil
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

# Node.js version for Playwright driver (must match Playwright's compatibility range)
_NODE_VERSION = '20.18.3'

# Bounded retry policy for the first-run downloads.
_MAX_ATTEMPTS = 3
_BACKOFF_BASE_SECONDS = 3.0  # 3s, 6s, 12s

# ---------------------------------------------------------------------------
# Provisioning status — readable by the health endpoint / UI / crawl entry.
# ---------------------------------------------------------------------------
# State values:
#   "pending"      — not started yet
#   "provisioning" — download/install in progress
#   "ready"        — component usable
#   "degraded"     — download/install failed; carries a user-facing reason
_STATUS_LOCK = threading.Lock()
_PROVISION_STATUS = {
    "node": {"state": "pending", "reason": None, "progress": None},
    "chromium": {"state": "pending", "reason": None, "progress": None},
}


def _set_status(component: str, state: str, *, reason=None, progress=None):
    """Update a component's provisioning status (thread-safe)."""
    with _STATUS_LOCK:
        entry = _PROVISION_STATUS[component]
        entry["state"] = state
        entry["reason"] = reason
        if progress is not None:
            entry["progress"] = progress
        elif state in ("ready", "pending"):
            entry["progress"] = None


def get_provisioning_status() -> dict:
    """Return a snapshot of browser-engine provisioning status.

    Shape::

        {
          "ready": bool,                 # both node + chromium usable
          "state": "ready"|"provisioning"|"degraded"|"pending",
          "node":     {"state","reason","progress"},
          "chromium": {"state","reason","progress"},
          "error": <user-facing string or None>,
        }

    Consumed by the local runner health endpoint so the UI shows a real
    "downloading / failed" state instead of a green "ready" that crawls then
    fail silently.
    """
    with _STATUS_LOCK:
        node = dict(_PROVISION_STATUS["node"])
        chromium = dict(_PROVISION_STATUS["chromium"])

    states = (node["state"], chromium["state"])
    if all(s == "ready" for s in states):
        overall = "ready"
    elif "degraded" in states:
        overall = "degraded"
    elif "provisioning" in states:
        overall = "provisioning"
    else:
        overall = "pending"

    return {
        "ready": overall == "ready",
        "state": overall,
        "node": node,
        "chromium": chromium,
        "error": browser_engine_error(),
    }


def browser_engine_error():
    """Return a precise, user-facing error string if the engine is unusable.

    Returns ``None`` when the engine is ready (or still provisioning without a
    failure). The crawl entry point should call this and surface the string
    verbatim instead of letting a generic ImportError / launch timeout bubble
    up. Example return::

        "Browser engine not installed — download failed: Node.js download
         failed: <urlopen error ...>. Reconnect and retry provisioning."
    """
    with _STATUS_LOCK:
        node = dict(_PROVISION_STATUS["node"])
        chromium = dict(_PROVISION_STATUS["chromium"])

    failed = []
    if node["state"] == "degraded":
        failed.append(f"Node.js runtime: {node['reason'] or 'unknown error'}")
    if chromium["state"] == "degraded":
        failed.append(f"Chromium browser: {chromium['reason'] or 'unknown error'}")

    if failed:
        return (
            "Browser engine not installed — download failed: "
            + "; ".join(failed)
            + ". Reconnect and retry provisioning."
        )

    # Not failed, but not ready yet → still downloading.
    if node["state"] != "ready" or chromium["state"] != "ready":
        if "provisioning" in (node["state"], chromium["state"]):
            return (
                "Browser engine is still downloading (~150 MB). "
                "Please wait for provisioning to finish, then retry."
            )
        return (
            "Browser engine not installed yet. "
            "Provisioning has not completed — retry once online."
        )
    return None


# ---------------------------------------------------------------------------
# Node.js
# ---------------------------------------------------------------------------

def _node_paths():
    """Return (node_dir, node_bin) for the current platform."""
    import platform as _platform
    node_dir = Path.home() / '.flyto' / 'node'
    if _platform.system() == 'Windows':
        return node_dir, node_dir / 'node.exe'
    return node_dir, node_dir / 'bin' / 'node'


def _fetch_node_checksum(filename: str) -> str:
    """Fetch the expected SHA-256 for ``filename`` from nodejs.org SHASUMS256.txt.

    Returns the hex digest, or "" if it could not be fetched (in which case we
    proceed without verification rather than block the install offline-style).
    """
    import urllib.request
    url = f"https://nodejs.org/dist/v{_NODE_VERSION}/SHASUMS256.txt"
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            text = resp.read().decode("utf-8", "replace")
        for line in text.splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1] == filename:
                return parts[0].strip()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Could not fetch Node.js checksum (continuing unverified): {e}")
    return ""


def _download_node_once(url: str, filename: str, node_dir: Path) -> bool:
    """Download + verify + extract node exactly once. Returns True on success.

    Idempotent / resumable: writes to a temp dir and only swaps the binary into
    place atomically once verified, so a half-written download never leaves a
    broken node behind.
    """
    import hashlib
    import io
    import tarfile
    import urllib.request
    import zipfile

    # Stream the download so we can emit progress for the (smaller) node file.
    try:
        req = urllib.request.urlopen(url, timeout=180)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Node.js download failed: {e}")
        _set_status("node", "degraded", reason=f"Node.js download failed: {e}")
        return False

    try:
        total = int(req.headers.get("Content-Length") or 0)
        chunks = []
        read = 0
        last_pct = -10
        while True:
            chunk = req.read(256 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
            read += len(chunk)
            if total:
                pct = int(read * 100 / total)
                if pct >= last_pct + 10:
                    last_pct = pct
                    logger.info(f"Downloading Node.js runtime... {pct}%")
                    _set_status("node", "provisioning", progress={"phase": "node", "percent": pct})
        data = b"".join(chunks)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Node.js download interrupted: {e}")
        _set_status("node", "degraded", reason=f"Node.js download interrupted: {e}")
        return False
    finally:
        try:
            req.close()
        except Exception:
            pass

    # Verify checksum when available (network fetch of SHASUMS256.txt).
    expected = _fetch_node_checksum(filename)
    if expected:
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            reason = f"Node.js checksum mismatch (expected {expected[:12]}…, got {actual[:12]}…)"
            logger.warning(reason)
            _set_status("node", "degraded", reason=reason)
            return False

    node_dir.mkdir(parents=True, exist_ok=True)
    # Stage into a temp path, then move atomically — resumable & never partial.
    tmp_bin = node_dir / ('node.exe.part' if filename.endswith('.zip') else 'node.part')
    try:
        if filename.endswith('.tar.gz'):
            with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tar:
                prefix = tar.getnames()[0].split('/')[0]
                member = None
                for m in tar.getmembers():
                    if m.name == f"{prefix}/bin/node":
                        member = m
                        break
                if member is None:
                    logger.warning("Node.js binary not found in archive")
                    _set_status("node", "degraded", reason="Node.js binary missing from archive")
                    return False
                src = tar.extractfile(member)
                tmp_bin.write_bytes(src.read())
                tmp_bin.chmod(0o755)
                final = node_dir / 'bin' / 'node'
                final.parent.mkdir(parents=True, exist_ok=True)
                os.replace(str(tmp_bin), str(final))
                return True
        elif filename.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                prefix = zf.namelist()[0].split('/')[0]
                target_name = f"{prefix}/node.exe"
                if target_name not in zf.namelist():
                    logger.warning("Node.js binary not found in archive")
                    _set_status("node", "degraded", reason="Node.js binary missing from archive")
                    return False
                tmp_bin.write_bytes(zf.read(target_name))
                final = node_dir / 'node.exe'
                os.replace(str(tmp_bin), str(final))
                return True
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Node.js extract failed: {e}")
        _set_status("node", "degraded", reason=f"Node.js extract failed: {e}")
        return False
    finally:
        if tmp_bin.exists():
            try:
                tmp_bin.unlink()
            except OSError:
                pass

    return False


async def ensure_node_binary():
    """Download Node.js binary to ~/.flyto/node/ if not already present.

    PyInstaller's bundled node crashes with "Failed to reserve virtual memory
    for CodeRange" due to V8 address space pressure from the 2 GB temp
    extraction. A standalone node binary at a stable path avoids this. We keep
    the runtime download (rather than fighting the V8 CodeRange reservation in
    the frozen process) but make it as robust as the chromium one: retry +
    backoff, checksum, atomic install, and a surfaced degraded state.
    """
    import platform as _platform

    node_dir, node_bin = _node_paths()
    if node_bin.exists():
        logger.info(f"Node.js already available: {node_bin}")
        _set_status("node", "ready")
        return

    system = _platform.system()
    machine = _platform.machine().lower()
    if system == 'Darwin':
        arch = 'arm64' if machine == 'arm64' else 'x64'
        filename = f"node-v{_NODE_VERSION}-darwin-{arch}.tar.gz"
    elif system == 'Windows':
        filename = f"node-v{_NODE_VERSION}-win-x64.zip"
    else:
        filename = f"node-v{_NODE_VERSION}-linux-x64.tar.gz"

    url = f"https://nodejs.org/dist/v{_NODE_VERSION}/{filename}"
    loop = asyncio.get_running_loop()

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        logger.info(
            f"Downloading Node.js v{_NODE_VERSION} for Playwright driver "
            f"(attempt {attempt}/{_MAX_ATTEMPTS})..."
        )
        _set_status("node", "provisioning",
                    progress={"phase": "node", "percent": 0, "attempt": attempt})
        try:
            ok = await loop.run_in_executor(
                None, lambda: _download_node_once(url, filename, node_dir)
            )
        except Exception as e:  # noqa: BLE001
            ok = False
            logger.warning(f"Node.js background install failed: {e}")
            _set_status("node", "degraded", reason=f"Node.js install crashed: {e}")

        if ok:
            logger.info(f"Node.js v{_NODE_VERSION} installed to {node_dir}")
            _set_status("node", "ready")
            return

        if attempt < _MAX_ATTEMPTS:
            delay = _BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            logger.warning(f"Node.js download failed, retrying in {delay:.0f}s...")
            await asyncio.sleep(delay)

    # All attempts exhausted — status already 'degraded' with a reason.
    with _STATUS_LOCK:
        if _PROVISION_STATUS["node"]["state"] != "degraded":
            _PROVISION_STATUS["node"]["state"] = "degraded"
            if not _PROVISION_STATUS["node"]["reason"]:
                _PROVISION_STATUS["node"]["reason"] = "Node.js download failed after retries"
    logger.warning("Node.js download failed after all retries — browser engine degraded")


# ---------------------------------------------------------------------------
# Playwright Chromium
# ---------------------------------------------------------------------------

def _clean_partial_chromium(browsers_dir: Path):
    """Remove half-written chromium-* dirs so a re-install is idempotent.

    A directory missing the expected executable marker indicates a download
    that was interrupted; leaving it makes Playwright think chromium exists
    and crawls then fail. We only delete dirs that look incomplete.
    """
    for d in browsers_dir.glob("chromium-*"):
        try:
            # A complete install has a chrome-* executable somewhere inside.
            has_exe = any(d.rglob("chrome")) or any(d.rglob("chrome.exe")) \
                or any(d.rglob("Chromium")) or any(d.rglob("headless_shell")) \
                or any(d.rglob("headless_shell.exe"))
            marker = d / "INSTALLATION_COMPLETE"
            if not has_exe and not marker.exists():
                logger.info(f"Cleaning partial chromium download: {d.name}")
                shutil.rmtree(d, ignore_errors=True)
        except Exception:  # noqa: BLE001
            # If we can't inspect it, leave it; install will validate later.
            pass


def _chromium_installed(browsers_dir: Path) -> bool:
    """True if a *complete* chromium install is present."""
    for d in browsers_dir.glob("chromium-*"):
        if (d / "INSTALLATION_COMPLETE").exists():
            return True
        if any(d.rglob("chrome")) or any(d.rglob("chrome.exe")) \
                or any(d.rglob("headless_shell")) or any(d.rglob("headless_shell.exe")):
            return True
    return False


def _run_chromium_install_once(driver_exe, driver_cli, env) -> "tuple[int, str]":
    """Run the playwright install subprocess once, streaming progress.

    Returns (returncode, last_stderr_tail). Progress lines from the driver
    (e.g. "Downloading Chromium ... 42%") are forwarded to ``logger`` (and thus
    the /ws/logs WebSocket) and reflected into the status progress field.
    """
    import re
    import subprocess

    proc = subprocess.Popen(
        [str(driver_exe), str(driver_cli), "install", "chromium"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        bufsize=1,
    )
    pct_re = re.compile(r"(\d{1,3})\s*%")
    tail = []
    last_logged = -10
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip()
            if not line:
                continue
            tail.append(line)
            if len(tail) > 8:
                tail.pop(0)
            m = pct_re.search(line)
            if m:
                pct = min(100, int(m.group(1)))
                if pct >= last_logged + 10:
                    last_logged = pct
                    logger.info(f"Downloading browser engine (Chromium)... {pct}%")
                    _set_status("chromium", "provisioning",
                                progress={"phase": "chromium", "percent": pct})
            elif "Downloading" in line or "Chromium" in line:
                logger.info(f"Browser engine: {line}")
    except Exception as e:  # noqa: BLE001
        tail.append(f"stream error: {e}")
    finally:
        try:
            proc.wait(timeout=600)
        except Exception:
            proc.kill()
    return proc.returncode if proc.returncode is not None else 1, "\n".join(tail)[:400]


def configure_playwright_browsers_path() -> Path:
    """Set and return the persistent browser directory for runner processes."""
    configured = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    browsers_dir = Path(configured).expanduser() if configured else Path.home() / ".flyto" / "browsers"
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_dir)
    return browsers_dir


async def ensure_playwright_chromium():
    """Download Playwright Chromium in background if not already present.

    Retries with backoff, cleans half-written downloads before each attempt,
    streams progress, and surfaces a degraded state with a precise reason on
    failure (instead of a single swallowed warning).
    """
    browsers_dir = configure_playwright_browsers_path()
    if not browsers_dir.exists():
        browsers_dir.mkdir(parents=True, exist_ok=True)

    if _chromium_installed(browsers_dir):
        logger.info("Playwright Chromium already available")
        _set_status("chromium", "ready")
        return

    try:
        from playwright._impl._driver import compute_driver_executable, get_driver_env
        driver_exe, driver_cli = compute_driver_executable()
        env = get_driver_env()
        env["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_dir)
    except Exception as e:  # noqa: BLE001
        reason = f"Playwright driver not available: {e}"
        logger.warning(reason)
        _set_status("chromium", "degraded", reason=reason)
        return

    loop = asyncio.get_running_loop()

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        # Idempotent: drop any partial dir from a prior interrupted attempt.
        _clean_partial_chromium(browsers_dir)

        logger.info(
            f"Downloading browser engine in background "
            f"(attempt {attempt}/{_MAX_ATTEMPTS})..."
        )
        _set_status("chromium", "provisioning",
                    progress={"phase": "chromium", "percent": 0, "attempt": attempt})

        try:
            returncode, tail = await loop.run_in_executor(
                None, lambda: _run_chromium_install_once(driver_exe, driver_cli, env)
            )
        except Exception as e:  # noqa: BLE001
            returncode, tail = 1, str(e)

        if returncode == 0 and _chromium_installed(browsers_dir):
            logger.info("Browser engine (Chromium) downloaded successfully")
            _set_status("chromium", "ready")
            return

        reason = (tail or "unknown error")[:300]
        logger.warning(f"Browser download failed (attempt {attempt}): {reason}")
        _set_status("chromium", "degraded", reason=reason)

        if attempt < _MAX_ATTEMPTS:
            delay = _BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            logger.warning(f"Browser download failed, retrying in {delay:.0f}s...")
            await asyncio.sleep(delay)

    logger.warning("Browser engine download failed after all retries — crawl will be unavailable")


# ---------------------------------------------------------------------------
# Re-triggerable provisioning entry point
# ---------------------------------------------------------------------------

# Guards against two concurrent provisioning runs (e.g. startup + a UI retry).
_PROVISION_LOCK = asyncio.Lock()


async def provision_browser_engine(force: bool = False) -> dict:
    """Run (or re-run) node + chromium provisioning. Safe to call repeatedly.

    This is the single entry point used both at startup and for a user-driven
    retry (e.g. someone who was offline on first launch). It does not require
    reinstalling the app.

    Args:
        force: if True, re-provision even components currently marked ready
               (e.g. to repair a corrupted install).

    Returns the provisioning status snapshot (see ``get_provisioning_status``).
    """
    async with _PROVISION_LOCK:
        if force:
            _set_status("node", "pending")
            _set_status("chromium", "pending")

        await asyncio.gather(
            ensure_node_binary(),
            ensure_playwright_chromium(),
            return_exceptions=True,
        )
    status = get_provisioning_status()
    if status["ready"]:
        logger.info("Browser engine provisioning complete — crawl available")
    else:
        logger.warning(
            "Browser engine provisioning incomplete: "
            + (status["error"] or status["state"])
        )
    return status
