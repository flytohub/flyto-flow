"""
Package installation, update, and removal operations.
"""

import sys
import shutil
import hashlib
import zipfile
import logging
import asyncio
import platform as _platform
from pathlib import Path
from typing import Optional

import aiohttp
from fastapi import HTTPException

from .models import PackageActionResult
from .package_defs import (
    _PACKAGES_BY_ID,
    _IS_FROZEN,
    _PIP_TARGET_DIR,
    _CACHE_DIR,
    _get_installed_version,
    _get_chromium_version,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Helpers — PyPI wheel download (no system Python required)
# =============================================================================

async def _get_pypi_wheel_info(pypi_url: str) -> Optional[dict]:
    """
    Fetch wheel download URL and SHA256 from PyPI JSON API.
    Returns dict with: version, download_url, filename, sha256
    """
    try:
        timeout = aiohttp.ClientTimeout(total=15, connect=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(pypi_url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        info = data.get("info", {})
        version = info.get("version", "")
        urls = data.get("urls", [])

        # Find compatible wheel: prefer py3-none-any, then platform-specific
        system = _platform.system().lower()
        machine = _platform.machine().lower()

        best_wheel = None
        for u in urls:
            if u.get("packagetype") != "bdist_wheel":
                continue
            fname = u.get("filename", "")
            # Pure Python wheel (works everywhere)
            if "py3-none-any" in fname:
                best_wheel = u
                break
            # Platform-specific: match OS + arch
            if system == "darwin" and "macosx" in fname:
                if machine in fname or "universal2" in fname or "x86_64" in fname:
                    best_wheel = u
            elif system == "linux" and "linux" in fname:
                if machine in fname or "x86_64" in fname:
                    best_wheel = u
            elif system == "windows" and "win" in fname:
                best_wheel = u

        if not best_wheel:
            # Fallback: any wheel
            for u in urls:
                if u.get("packagetype") == "bdist_wheel":
                    best_wheel = u
                    break

        if not best_wheel:
            logger.warning("No wheel found at %s", pypi_url)
            return None

        digests = best_wheel.get("digests", {})
        return {
            "version": version,
            "download_url": best_wheel["url"],
            "filename": best_wheel["filename"],
            "sha256": digests.get("sha256", ""),
        }
    except Exception as e:
        logger.error("Failed to get wheel info from %s: %s", pypi_url, e)
        return None


async def _download_and_install_wheel(
    pypi_url: str,
    pip_name: str,
    package_id: str,
    upgrade: bool = False,
) -> PackageActionResult:
    """
    Download a wheel from PyPI and extract it to pip_packages dir.
    No system Python required — uses zipfile from stdlib.
    """
    pkg = _PACKAGES_BY_ID.get(package_id)
    old_version = _get_installed_version(pkg) if pkg else None

    # Check if already installed and not upgrading
    if old_version and not upgrade:
        return PackageActionResult(
            ok=True,
            message="Already installed",
            package_id=package_id,
            from_version=old_version,
            to_version=old_version,
        )

    # Get wheel info from PyPI
    wheel_info = await _get_pypi_wheel_info(pypi_url)
    if not wheel_info:
        return PackageActionResult(
            ok=False,
            message="Failed to find package on PyPI",
            package_id=package_id,
        )

    # Skip if already on latest
    if old_version and old_version == wheel_info["version"] and upgrade:
        return PackageActionResult(
            ok=True,
            message="Already on latest version",
            package_id=package_id,
            from_version=old_version,
            to_version=old_version,
        )

    logger.info("Downloading %s %s from PyPI...", pip_name, wheel_info["version"])

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _PIP_TARGET_DIR.mkdir(parents=True, exist_ok=True)
    whl_path = _CACHE_DIR / wheel_info["filename"]

    try:
        # Download wheel
        sha256 = hashlib.sha256()
        timeout = aiohttp.ClientTimeout(total=300, connect=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(wheel_info["download_url"]) as resp:
                if resp.status != 200:
                    return PackageActionResult(
                        ok=False,
                        message="Download failed: HTTP {}".format(resp.status),
                        package_id=package_id,
                    )
                with open(whl_path, 'wb') as f:
                    while True:
                        chunk = await resp.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        sha256.update(chunk)

        # Verify SHA256
        expected_sha = wheel_info.get("sha256")
        if expected_sha:
            actual_sha = sha256.hexdigest()
            if actual_sha != expected_sha:
                logger.error("SHA256 mismatch for %s: expected %s, got %s",
                             pip_name, expected_sha[:16], actual_sha[:16])
                whl_path.unlink(missing_ok=True)
                return PackageActionResult(
                    ok=False,
                    message="Download verification failed (SHA256 mismatch)",
                    package_id=package_id,
                )

        # Remove old version from target dir before extracting new one
        if upgrade and old_version:
            _remove_from_target_dir(pip_name)

        # Extract wheel (it's a zip) directly to pip_packages
        with zipfile.ZipFile(whl_path, 'r') as zf:
            zf.extractall(_PIP_TARGET_DIR)

        # Cleanup downloaded wheel
        whl_path.unlink(missing_ok=True)

        # Ensure pip_packages is on sys.path
        target_str = str(_PIP_TARGET_DIR)
        if target_str not in sys.path:
            sys.path.insert(0, target_str)

        # Invalidate importlib caches so version detection picks up new install
        import importlib
        importlib.invalidate_caches()

        new_version = wheel_info["version"]
        logger.info("Installed %s %s to %s", pip_name, new_version, _PIP_TARGET_DIR)

        return PackageActionResult(
            ok=True,
            message="Updated successfully" if upgrade else "Installed successfully",
            package_id=package_id,
            from_version=old_version,
            to_version=new_version,
        )

    except Exception as e:
        logger.error("Wheel install error for %s: %s", pip_name, e)
        whl_path.unlink(missing_ok=True)
        return PackageActionResult(
            ok=False,
            message="Install error: {}".format(str(e)[:200]),
            package_id=package_id,
        )


# =============================================================================
# Helpers — Subprocess (dev mode only)
# =============================================================================

async def _run_subprocess(args: list, timeout: int = 120, extra_env: dict = None) -> tuple:
    """Run a subprocess asynchronously. Returns (returncode, stdout, stderr)."""
    import os
    env = None
    if extra_env:
        env = os.environ.copy()
        env.update(extra_env)
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        return (
            proc.returncode,
            stdout.decode('utf-8', errors='replace'),
            stderr.decode('utf-8', errors='replace'),
        )
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        raise


# =============================================================================
# Install strategies
# =============================================================================

async def _hot_update_core(force: bool = False) -> PackageActionResult:
    """
    Update flyto-core via HotUpdater (download wheel -> extract -> hot-reload).
    This is the correct mechanism for frozen mode.
    """
    try:
        from services.infra.updater import get_core_updater
        updater = get_core_updater()
        old_version = updater.current_version

        result = await updater.update_core(force=force)

        if result.get("error"):
            return PackageActionResult(
                ok=False,
                message="Update failed: {}".format(result["error"]),
                package_id='flyto-core',
                from_version=old_version,
            )

        if not result.get("updated"):
            return PackageActionResult(
                ok=True,
                message="Already on latest version",
                package_id='flyto-core',
                from_version=old_version,
                to_version=old_version,
            )

        return PackageActionResult(
            ok=True,
            message="Updated successfully via hot-update",
            package_id='flyto-core',
            from_version=old_version,
            to_version=result.get("to_version"),
        )
    except Exception as e:
        logger.error("Hot-update core error: %s", e)
        return PackageActionResult(
            ok=False,
            message="Hot-update error: {}".format(str(e)[:200]),
            package_id='flyto-core',
        )


async def _pip_install_dev(pip_name: str, package_id: str, upgrade: bool = False) -> PackageActionResult:
    """Install/update a pip package in dev mode (standard pip install)."""
    python = sys.executable
    pkg = _PACKAGES_BY_ID.get(package_id)
    old_version = _get_installed_version(pkg) if pkg else None

    args = [python, '-m', 'pip', 'install']
    if upgrade:
        args.append('--upgrade')
    args.append(pip_name)

    try:
        returncode, stdout, stderr = await _run_subprocess(args, timeout=120)
        if returncode != 0:
            return PackageActionResult(
                ok=False,
                message="Install failed: {}".format(stderr.strip()[:200]),
                package_id=package_id,
            )

        # Dev mode installs to site-packages, but _get_installed_version
        # checks ~/.flyto/pip_packages/ FIRST (frozen mode dir). If stale
        # dist-info exists there, it returns the wrong version forever.
        # Fix: remove stale entries from pip_packages after dev-mode install.
        if _PIP_TARGET_DIR.exists() and pip_name:
            _remove_from_target_dir(pip_name)

        # Invalidate importlib caches
        import importlib
        importlib.invalidate_caches()

        new_version = _get_installed_version(pkg) if pkg else None
        return PackageActionResult(
            ok=True,
            message="Updated successfully" if upgrade else "Installed successfully",
            package_id=package_id,
            from_version=old_version,
            to_version=new_version,
        )
    except asyncio.TimeoutError:
        return PackageActionResult(
            ok=False, message="Operation timed out", package_id=package_id,
        )
    except Exception as e:
        logger.error("pip install error [%s]: %s", package_id, e)
        return PackageActionResult(
            ok=False, message="Install error: {}".format(str(e)[:200]), package_id=package_id,
        )


async def _install_or_update_package(package_id: str, upgrade: bool = False) -> PackageActionResult:
    """
    Route install/update to the correct strategy based on package type and mode.
    """
    pkg = _PACKAGES_BY_ID.get(package_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    # --- Chromium: browser binary download (works in all modes) ---
    if package_id == 'chromium':
        return await _install_chromium()

    # --- flyto-core in frozen mode: use HotUpdater ---
    if package_id == 'flyto-core' and _IS_FROZEN:
        return await _hot_update_core(force=True)

    # --- All pip packages ---
    pip_name = pkg.get('pip_name')
    if not pip_name:
        raise HTTPException(status_code=400, detail="Package cannot be installed")

    pypi_url = pkg.get('pypi_url')
    if not pypi_url:
        raise HTTPException(status_code=400, detail="Package has no PyPI source")

    if _IS_FROZEN:
        # Frozen mode: download wheel directly, no system Python needed
        return await _download_and_install_wheel(pypi_url, pip_name, package_id, upgrade=upgrade)
    else:
        # Dev mode: standard pip install
        return await _pip_install_dev(pip_name, package_id, upgrade=upgrade)


async def _install_chromium() -> PackageActionResult:
    """
    Install Chromium browser via Playwright's bundled driver.
    Uses playwright._impl._driver directly — no system Python needed.
    """
    import os

    browsers_dir = Path(os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(Path.home() / '.flyto' / 'browsers'),
    ))
    browsers_dir.mkdir(parents=True, exist_ok=True)

    # Quick check: already installed?
    chromium_dirs = list(browsers_dir.glob("chromium-*"))
    if chromium_dirs:
        return PackageActionResult(
            ok=True,
            message="Chromium already installed",
            package_id='chromium',
            to_version=_get_chromium_version(),
        )

    try:
        # Use playwright's bundled driver directly (same approach as browser_bootstrap.py)
        from playwright._impl._driver import compute_driver_executable, get_driver_env
        driver_exe, driver_cli = compute_driver_executable()
        env = get_driver_env()
        env["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_dir)
    except ImportError:
        # Playwright not installed — install it first via wheel download
        pw_pkg = _PACKAGES_BY_ID.get('playwright')
        if pw_pkg and pw_pkg.get('pypi_url'):
            pw_result = await _download_and_install_wheel(
                pw_pkg['pypi_url'], 'playwright', 'playwright',
            )
            if not pw_result.ok:
                return PackageActionResult(
                    ok=False,
                    message="Playwright must be installed first. {}".format(pw_result.message),
                    package_id='chromium',
                )
            # Retry after installing playwright
            try:
                from playwright._impl._driver import compute_driver_executable, get_driver_env
                driver_exe, driver_cli = compute_driver_executable()
                env = get_driver_env()
                env["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_dir)
            except ImportError:
                return PackageActionResult(
                    ok=False,
                    message="Playwright installed but driver not available. Please restart the app.",
                    package_id='chromium',
                )
        else:
            return PackageActionResult(
                ok=False,
                message="Playwright is required to install Chromium",
                package_id='chromium',
            )
    except Exception as e:
        return PackageActionResult(
            ok=False,
            message="Playwright driver error: {}".format(str(e)[:200]),
            package_id='chromium',
        )

    try:
        loop = asyncio.get_running_loop()
        import subprocess
        result = await loop.run_in_executor(None, lambda: subprocess.run(
            [str(driver_exe), str(driver_cli), "install", "chromium"],
            capture_output=True, text=True, timeout=600, env=env,
        ))

        if result.returncode != 0:
            stderr = result.stderr[:200] if result.stderr else "unknown error"
            return PackageActionResult(
                ok=False,
                message="Chromium install failed: {}".format(stderr),
                package_id='chromium',
            )

        new_version = _get_chromium_version()
        return PackageActionResult(
            ok=True,
            message="Chromium installed successfully",
            package_id='chromium',
            to_version=new_version,
        )
    except Exception as e:
        logger.error("Chromium install error: %s", e)
        return PackageActionResult(
            ok=False,
            message="Chromium install error: {}".format(str(e)[:200]),
            package_id='chromium',
        )


async def _remove_package_impl(package_id: str) -> PackageActionResult:
    """Remove a package using the correct strategy."""
    pkg = _PACKAGES_BY_ID.get(package_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    if not pkg['removable']:
        raise HTTPException(status_code=400, detail="This package cannot be removed")

    if not _get_installed_version(pkg):
        return PackageActionResult(
            ok=False, message="Package is not installed", package_id=package_id,
        )

    # --- Chromium: remove browser binary ---
    if package_id == 'chromium':
        return await _remove_chromium()

    # --- Pip packages in frozen mode: remove from target dir (no Python needed) ---
    pip_name = pkg.get('pip_name')
    if not pip_name:
        raise HTTPException(status_code=400, detail="Package cannot be removed")

    if _IS_FROZEN:
        removed = _remove_from_target_dir(pip_name)
        if removed:
            return PackageActionResult(ok=True, message="Removed successfully", package_id=package_id)
        return PackageActionResult(
            ok=False, message="Package files not found in install directory", package_id=package_id,
        )

    # --- Dev mode: standard pip uninstall ---
    try:
        args = [sys.executable, '-m', 'pip', 'uninstall', '-y', pip_name]
        returncode, stdout, stderr = await _run_subprocess(args, timeout=60)

        if returncode != 0:
            return PackageActionResult(
                ok=False,
                message="Remove failed: {}".format(stderr.strip()[:200]),
                package_id=package_id,
            )
        return PackageActionResult(ok=True, message="Removed successfully", package_id=package_id)

    except Exception as e:
        logger.error("Package remove error [%s]: %s", package_id, e)
        return PackageActionResult(
            ok=False, message="Remove error: {}".format(str(e)[:200]), package_id=package_id,
        )


async def _remove_chromium() -> PackageActionResult:
    """Remove Chromium browser binary."""
    import os

    browsers_dir = Path(os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(Path.home() / '.flyto' / 'browsers'),
    ))

    if not browsers_dir.exists():
        return PackageActionResult(
            ok=False, message="Browser directory not found", package_id='chromium',
        )

    # Try playwright driver first (cleanest removal)
    try:
        from playwright._impl._driver import compute_driver_executable, get_driver_env
        driver_exe, driver_cli = compute_driver_executable()
        env = get_driver_env()
        env["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_dir)

        import subprocess
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: subprocess.run(
            [str(driver_exe), str(driver_cli), "uninstall", "chromium"],
            capture_output=True, text=True, timeout=120, env=env,
        ))
        if result.returncode == 0:
            return PackageActionResult(ok=True, message="Removed successfully", package_id='chromium')
    except Exception:
        pass

    # Fallback: delete chromium directories directly
    try:
        removed = False
        for item in browsers_dir.iterdir():
            if item.name.startswith('chromium') and item.is_dir():
                shutil.rmtree(item)
                removed = True
        if removed:
            return PackageActionResult(ok=True, message="Removed successfully", package_id='chromium')
        return PackageActionResult(ok=False, message="Chromium not found", package_id='chromium')
    except Exception as e:
        return PackageActionResult(
            ok=False, message="Remove error: {}".format(str(e)[:200]), package_id='chromium',
        )


def _remove_from_target_dir(pip_name: str) -> bool:
    """Remove a package from the pip_packages target directory."""
    if not _PIP_TARGET_DIR.exists():
        return False

    # Normalize package name for directory matching (e.g., flyto-ai -> flyto_ai)
    normalized = pip_name.replace('-', '_').lower()

    # Collect items to remove first, then delete (avoid modifying dir while iterating)
    to_remove = []
    for item in _PIP_TARGET_DIR.iterdir():
        name_lower = item.name.lower().replace('-', '_')
        # Match: flyto_ai (package dir), flyto_ai-0.9.27.dist-info, flyto_ai-0.9.27.data
        # After replace('-','_'), separator becomes '_', so check both
        if name_lower == normalized or name_lower.startswith(normalized + '-') or name_lower.startswith(normalized + '_'):
            to_remove.append(item)

    for item in to_remove:
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception as e:
            logger.warning("Failed to remove %s: %s", item, e)

    return len(to_remove) > 0
