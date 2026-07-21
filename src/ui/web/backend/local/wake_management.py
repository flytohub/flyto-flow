"""
Wake Daemon Management Routes

Enable/disable/status endpoints for the remote wake daemon,
plus OS-specific service install/uninstall helpers.

Extracted from main_local.py.
"""

import logging
import os
import sys
from pathlib import Path

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wake-daemon", tags=["wake-daemon"])


class _WakeDeps:
    """Injected dependencies for wake daemon handlers."""

    __slots__ = ("get_device_id", "get_captured_token", "get_proxy_client_bound", "cloud_api_url")

    def __init__(self, *, get_device_id, get_captured_token, get_proxy_client_bound, cloud_api_url: str):
        self.get_device_id = get_device_id
        self.get_captured_token = get_captured_token
        self.get_proxy_client_bound = get_proxy_client_bound
        self.cloud_api_url = cloud_api_url


async def _handle_wake_enable(deps: _WakeDeps, body: dict) -> dict:
    """Enable remote wake: write config + install system service + set cloud flag."""
    import json as _json
    from pathlib import Path as _Path

    refresh_token = body.get("refresh_token")
    app_path = body.get("app_path")

    if not refresh_token:
        return {"ok": False, "error": "Missing refresh_token"}

    device_id = deps.get_device_id()
    identity_refresh_url = f"{deps.cloud_api_url.rstrip('/')}/api/auth/refresh"

    flyto_dir = _Path.home() / ".flyto"
    flyto_dir.mkdir(parents=True, exist_ok=True)

    # Auto-detect app_path if not provided
    if not app_path:
        import platform as _platform
        system = _platform.system()
        if system == "Darwin":
            for candidate in ["/Applications/Flyto2.app", os.path.expanduser("~/Applications/Flyto2.app")]:
                if os.path.exists(candidate):
                    app_path = candidate
                    break
        elif system == "Windows":
            for candidate in [
                os.path.expandvars(r"%LOCALAPPDATA%\Flyto2\Flyto2.exe"),
                os.path.expandvars(r"%PROGRAMFILES%\Flyto2\Flyto2.exe"),
            ]:
                if os.path.exists(candidate):
                    app_path = candidate
                    break

    # Write daemon config
    config = {
        "device_id": device_id,
        "cloud_api_url": deps.cloud_api_url,
        "refresh_token": refresh_token,
        "identity_refresh_url": identity_refresh_url,
        "app_path": app_path,
    }
    config_path = flyto_dir / "wake_daemon.json"
    config_path.write_text(_json.dumps(config, indent=2), encoding="utf-8")

    # Find the bundled flyto2-wake binary
    wake_binary = _find_wake_binary()
    if not wake_binary:
        return {"ok": False, "error": "Wake daemon binary not found in application bundle"}

    # Install as system service
    import platform as _platform
    system = _platform.system()

    try:
        if system == "Darwin":
            _install_launchagent(wake_binary, "")
        elif system == "Windows":
            _install_windows_task(wake_binary, "")
        elif system == "Linux":
            _install_systemd_service(wake_binary, "")

        logger.info(f"Wake daemon enabled for device {device_id}")
    except Exception as e:
        logger.error(f"Failed to install wake daemon: {e}")
        return {"ok": False, "error": str(e)}

    # Set cloud flag so mobile app knows wake is available
    token = deps.get_captured_token()
    if token and deps.cloud_api_url:
        try:
            client = await deps.get_proxy_client_bound()
            await client.post(
                f"/api/devices/{device_id}/remote-wake-setting",
                json={"enabled": True},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
        except Exception as e:
            logger.warning(f"Failed to set cloud wake flag: {e}")

    return {"ok": True, "status": "enabled"}


async def _handle_wake_disable(deps: _WakeDeps) -> dict:
    """Disable remote wake: remove config + uninstall service + clear cloud flag."""
    from pathlib import Path as _Path

    flyto_dir = _Path.home() / ".flyto"
    config_path = flyto_dir / "wake_daemon.json"

    # Remove config (daemon auto-exits on next poll)
    if config_path.exists():
        config_path.unlink()

    # Uninstall system service
    import platform as _platform
    system = _platform.system()

    try:
        if system == "Darwin":
            _uninstall_launchagent()
        elif system == "Windows":
            _uninstall_windows_task()
        elif system == "Linux":
            _uninstall_systemd_service()

        logger.info("Wake daemon disabled")
    except Exception as e:
        logger.error(f"Failed to uninstall wake daemon: {e}")

    # Clear cloud flag
    device_id = deps.get_device_id()
    token = deps.get_captured_token()
    if token and deps.cloud_api_url:
        try:
            client = await deps.get_proxy_client_bound()
            await client.post(
                f"/api/devices/{device_id}/remote-wake-setting",
                json={"enabled": False},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
        except Exception as e:
            logger.warning(f"Failed to clear cloud wake flag: {e}")

    return {"ok": True, "status": "disabled"}


def _handle_wake_status() -> dict:
    """Check if wake daemon is installed and running."""
    from pathlib import Path as _Path

    config_path = _Path.home() / ".flyto" / "wake_daemon.json"
    config_exists = config_path.exists()

    import platform as _platform
    system = _platform.system()
    service_installed = False

    try:
        if system == "Darwin":
            plist = _Path.home() / "Library" / "LaunchAgents" / "com.flyto2.wake-daemon.plist"
            service_installed = plist.exists()
        elif system == "Windows":
            import subprocess as _sp
            result = _sp.run(
                ["schtasks", "/Query", "/TN", "Flyto2WakeDaemon"],
                capture_output=True, timeout=5,
            )
            service_installed = result.returncode == 0
        elif system == "Linux":
            service_file = _Path.home() / ".config" / "systemd" / "user" / "flyto-wake.service"
            service_installed = service_file.exists()
    except Exception:
        pass

    return {
        "ok": True,
        "config_exists": config_exists,
        "service_installed": service_installed,
        "enabled": config_exists and service_installed,
    }


def create_wake_management_router(
    *,
    get_device_id,
    get_captured_token,
    get_proxy_client_bound,
    cloud_api_url: str,
) -> APIRouter:
    """Create the wake daemon management router with injected dependencies.

    Args:
        get_device_id: Callable returning the current device ID.
        get_captured_token: Callable returning the captured auth token.
        get_proxy_client_bound: Async callable returning the proxy HTTP client.
        cloud_api_url: Cloud API base URL.
    """
    deps = _WakeDeps(
        get_device_id=get_device_id,
        get_captured_token=get_captured_token,
        get_proxy_client_bound=get_proxy_client_bound,
        cloud_api_url=cloud_api_url,
    )
    r = APIRouter(prefix="/api/wake-daemon", tags=["wake-daemon"])

    @r.post("/enable")
    async def wake_daemon_enable(request: Request):
        body = await request.json()
        return await _handle_wake_enable(deps, body)

    @r.post("/disable")
    async def wake_daemon_disable():
        return await _handle_wake_disable(deps)

    @r.get("/status")
    async def wake_daemon_status():
        return _handle_wake_status()

    return r


# --- Helper functions (module-level, used by route handlers) ---


def _find_wake_binary() -> str | None:
    """Find the bundled flyto2-wake binary (Tauri sidecar).

    Searches relative to the running binary (works for both dev and frozen).
    Returns the absolute path or None if not found.
    """
    import platform as _platform
    from pathlib import Path as _Path

    system = _platform.system()
    machine = _platform.machine().lower()

    # Determine the Tauri target triple
    if system == "Darwin":
        arch = "aarch64" if machine == "arm64" else "x86_64"
        triple = f"{arch}-apple-darwin"
        binary_name = f"flyto2-wake-{triple}"
        # Tauri's externalBin renames the sidecar to the bare configured name
        # ("binaries/flyto2-wake") and strips the triple suffix at bundle time.
        bundled_name = "flyto2-wake"
    elif system == "Windows":
        triple = "x86_64-pc-windows-msvc"
        binary_name = f"flyto2-wake-{triple}.exe"
        bundled_name = "flyto2-wake.exe"
    else:  # Linux
        triple = "x86_64-unknown-linux-gnu"
        binary_name = f"flyto2-wake-{triple}"
        bundled_name = "flyto2-wake"

    # In frozen mode (PyInstaller/Tauri bundle): binary is next to the executable
    if getattr(sys, 'frozen', False):
        exe_dir = _Path(sys.executable).resolve().parent
        # Tauri places sidecar binaries next to the main exe. At bundle time it
        # renames the triple-suffixed source file to the bare configured name,
        # so probe the suffix-stripped name first, then the suffixed name as a
        # dev/fallback convention.
        for parent in ([exe_dir, exe_dir.parent] if system == "Darwin" else [exe_dir]):
            for name in (bundled_name, binary_name):
                candidate = parent / name
                if candidate.exists():
                    return str(candidate)

    # Dev mode: check the Tauri binaries directory
    # __file__ is in flyto-cloud/src/ui/web/backend/local/wake_management.py
    # -> parent = local/, parent.parent = backend/, we need ../../frontend/
    frontend_dir = _Path(__file__).resolve().parent.parent.parent / "frontend"
    candidates = [
        frontend_dir / "src-tauri" / "binaries" / binary_name,
        frontend_dir / "src-tauri" / "flyto2-wake" / "target" / "release" / (
            "flyto2-wake.exe" if system == "Windows" else "flyto2-wake"
        ),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    # Also check ~/.flyto/ (copied there by previous install)
    home_candidate = _Path.home() / ".flyto" / binary_name
    if home_candidate.exists():
        return str(home_candidate)

    return None


def _install_launchagent(binary_path: str, _unused: str = ""):
    """Install macOS LaunchAgent for wake daemon.

    Uses `launchctl bootstrap` on macOS 13+ (Ventura) and falls back to
    `launchctl load` on older versions for compatibility.
    """
    import subprocess as _sp

    label = "com.flyto2.wake-daemon"
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_dir.mkdir(parents=True, exist_ok=True)
    plist_path = plist_dir / f"{label}.plist"

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{binary_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{Path.home() / ".flyto" / "wake_daemon_stdout.log"}</string>
    <key>StandardErrorPath</key>
    <string>{Path.home() / ".flyto" / "wake_daemon_stderr.log"}</string>
</dict>
</plist>
"""
    plist_path.write_text(plist_content, encoding="utf-8")

    # Unload any existing instance first (ignore errors if not loaded)
    gui_domain = f"gui/{os.getuid()}"
    _sp.run(["launchctl", "bootout", gui_domain, str(plist_path)],
            capture_output=True)

    # Try modern API first (macOS 13+), fall back to legacy
    result = _sp.run(["launchctl", "bootstrap", gui_domain, str(plist_path)],
                     capture_output=True)
    if result.returncode != 0:
        _sp.run(["launchctl", "load", str(plist_path)], check=True)


def _uninstall_launchagent():
    """Remove macOS LaunchAgent."""
    import subprocess as _sp

    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.flyto2.wake-daemon.plist"
    if plist_path.exists():
        gui_domain = f"gui/{os.getuid()}"
        # Try modern API first, then legacy
        result = _sp.run(["launchctl", "bootout", gui_domain, str(plist_path)],
                         capture_output=True)
        if result.returncode != 0:
            _sp.run(["launchctl", "unload", str(plist_path)], capture_output=True)
        plist_path.unlink()


def _install_windows_task(binary_path: str, _unused: str = ""):
    """Install Windows Task Scheduler entry for wake daemon."""
    import subprocess as _sp

    _sp.run([
        "schtasks", "/Create",
        "/TN", "Flyto2WakeDaemon",
        "/TR", f'"{binary_path}"',
        "/SC", "ONLOGON",
        "/RL", "LIMITED",
        "/F",
    ], check=True)

    # Start it immediately
    _sp.run(["schtasks", "/Run", "/TN", "Flyto2WakeDaemon"], capture_output=True)


def _uninstall_windows_task():
    """Remove Windows Task Scheduler entry."""
    import subprocess as _sp
    _sp.run(["schtasks", "/Delete", "/TN", "Flyto2WakeDaemon", "/F"], capture_output=True)


def _install_systemd_service(binary_path: str, _unused: str = ""):
    """Install systemd user service for wake daemon."""
    import subprocess as _sp

    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)
    service_path = service_dir / "flyto-wake.service"

    service_content = f"""[Unit]
Description=Flyto2 Remote Wake Daemon
After=network-online.target

[Service]
Type=simple
ExecStart={binary_path}
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
"""
    service_path.write_text(service_content, encoding="utf-8")
    _sp.run(["systemctl", "--user", "daemon-reload"], check=True)
    _sp.run(["systemctl", "--user", "enable", "--now", "flyto-wake.service"], check=True)


def _uninstall_systemd_service():
    """Remove systemd user service."""
    import subprocess as _sp

    service_path = Path.home() / ".config" / "systemd" / "user" / "flyto-wake.service"
    _sp.run(["systemctl", "--user", "disable", "--now", "flyto-wake.service"], capture_output=True)
    if service_path.exists():
        service_path.unlink()
    _sp.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
