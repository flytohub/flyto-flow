"""
Remote Wake Daemon

Lightweight background script that polls the cloud API for wake commands
and launches the Flyto2 desktop app when triggered.

Installed as a system service (LaunchAgent / Task Scheduler / systemd)
when the user enables "Remote Wake" in the desktop app settings.

Config file: ~/.flyto/wake_daemon.json
"""

import json
import logging
import os
import platform
import subprocess
import sys
import time
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import SplitResult, urlsplit

# Configure logging
_log_dir = Path.home() / ".flyto"
_log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(_log_dir / "wake_daemon.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("wake_daemon")

CONFIG_PATH = Path.home() / ".flyto" / "wake_daemon.json"
POLL_INTERVAL = 30  # seconds
MAX_TOKEN_FAILURES = 60  # ~30 min of retries before giving up


_cached_token = None
_token_expires_at = 0


def _validated_endpoint(value: str) -> "SplitResult | None":
    """Accept HTTPS endpoints and explicit loopback development endpoints."""
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except (TypeError, ValueError):
        return None
    if not host or parsed.username or parsed.password or parsed.fragment:
        return None
    try:
        is_loopback = host == "localhost" or ip_address(host).is_loopback
    except ValueError:
        is_loopback = False
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and is_loopback
    ):
        return None
    _ = port
    return parsed


def validate_wake_endpoints(cloud_url: str, refresh_url: str) -> bool:
    """Prevent wake credentials from crossing deployment origins."""
    cloud = _validated_endpoint(cloud_url)
    refresh = _validated_endpoint(refresh_url)
    if not cloud or not refresh:
        return False
    cloud_port = cloud.port or (443 if cloud.scheme == "https" else 80)
    refresh_port = refresh.port or (443 if refresh.scheme == "https" else 80)
    return (
        cloud.scheme,
        cloud.hostname,
        cloud_port,
    ) == (
        refresh.scheme,
        refresh.hostname,
        refresh_port,
    )


def _open_no_redirect(request, timeout: int):
    """Open one request without forwarding credentials across redirects."""
    import urllib.request

    class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    return urllib.request.build_opener(_NoRedirectHandler()).open(
        request,
        timeout=timeout,
    )


def load_config() -> "dict | None":
    """Load daemon config. Returns None if config file is missing (daemon disabled)."""
    if not CONFIG_PATH.exists():
        return None
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load config: {e}")
        return None


def refresh_access_token(
    refresh_token: str,
    refresh_url: str,
    cloud_url: str,
) -> "str | None":
    """Exchange a refresh token for a fresh access token. Caches for 50 min."""
    global _cached_token, _token_expires_at

    if not validate_wake_endpoints(cloud_url, refresh_url):
        logger.error("Unsafe wake endpoint configuration")
        return None

    now = time.time()
    if _cached_token and now < _token_expires_at:
        return _cached_token

    try:
        import urllib.request

        data = json.dumps({
            "refresh_token": refresh_token,
        }).encode()

        req = urllib.request.Request(
            refresh_url,
            data=data,
            headers={
                "Content-Type": "application/json",
            },
        )

        with _open_no_redirect(req, timeout=15) as resp:
            result = json.loads(resp.read())
            token = result.get("access_token") or result.get("id_token")
            if token:
                _cached_token = token
                # Provider access tokens typically last 3600s; refresh at 50 min.
                _token_expires_at = now + 3000
            return token
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        return None


def poll_wake(cloud_url: str, device_id: str, id_token: str) -> bool:
    """Poll for pending wake commands. Returns True if wake needed.

    The wake-poll endpoint also records daemon heartbeat on the server side,
    so no separate heartbeat call is needed.
    """
    if _validated_endpoint(cloud_url) is None:
        logger.error("Unsafe cloud API endpoint configuration")
        return False
    try:
        import urllib.request

        url = f"{cloud_url}/api/devices/{device_id}/wake-poll"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {id_token}"},
        )

        with _open_no_redirect(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if result.get("wake"):
                logger.info(f"Wake command received: {result.get('command_id')}")
                return True
    except Exception as e:
        logger.warning(f"Poll failed: {e}")
    return False


def launch_desktop_app(app_path: "str | None" = None):
    """Launch the Flyto2 desktop app."""
    system = platform.system()

    try:
        if system == "Darwin":
            path = app_path or "/Applications/Flyto2.app"
            if os.path.exists(path):
                subprocess.Popen(["open", path])
                logger.info(f"Launched: {path}")
            else:
                # Try spotlight
                subprocess.Popen(["open", "-a", "Flyto2"])
                logger.info("Launched via spotlight: Flyto2")

        elif system == "Windows":
            path = app_path
            if path and os.path.exists(path):
                subprocess.Popen([path], shell=False)
                logger.info(f"Launched: {path}")
            else:
                # Try common locations
                for candidate in [
                    os.path.expandvars(r"%LOCALAPPDATA%\Flyto2\Flyto2.exe"),
                    os.path.expandvars(r"%PROGRAMFILES%\Flyto2\Flyto2.exe"),
                ]:
                    if os.path.exists(candidate):
                        subprocess.Popen([candidate], shell=False)
                        logger.info(f"Launched: {candidate}")
                        return
                logger.error("Desktop app not found")

        elif system == "Linux":
            path = app_path
            if path and os.path.exists(path):
                subprocess.Popen([path])
                logger.info(f"Launched: {path}")
            else:
                # Try common locations
                for candidate in [
                    os.path.expanduser("~/.local/bin/flyto2"),
                    "/usr/bin/flyto2",
                    "/opt/flyto2/flyto2",
                ]:
                    if os.path.exists(candidate):
                        subprocess.Popen([candidate])
                        logger.info(f"Launched: {candidate}")
                        return
                logger.error("Desktop app not found")

    except Exception as e:
        logger.error(f"Failed to launch desktop app: {e}")


def main():
    """Main daemon loop."""
    logger.info("Wake daemon started")

    consecutive_failures = 0

    while True:
        # Check config every loop — auto-exit if config deleted (user disabled)
        config = load_config()
        if not config:
            logger.info("Config file removed — daemon exiting")
            break

        device_id = config.get("device_id")
        cloud_url = config.get("cloud_api_url", "").rstrip("/")
        refresh_token = config.get("refresh_token")
        identity_refresh_url = config.get("identity_refresh_url") or f"{cloud_url}/api/auth/refresh"
        app_path = config.get("app_path")

        if not all([device_id, cloud_url, refresh_token, identity_refresh_url]):
            logger.error("Incomplete config — waiting for fix")
            time.sleep(POLL_INTERVAL)
            continue

        if not validate_wake_endpoints(cloud_url, identity_refresh_url):
            logger.error("Unsafe wake endpoint configuration — waiting for fix")
            _cached_token = None
            time.sleep(POLL_INTERVAL)
            continue

        # Refresh access token
        id_token = refresh_access_token(
            refresh_token,
            identity_refresh_url,
            cloud_url,
        )
        if not id_token:
            consecutive_failures += 1
            if consecutive_failures > MAX_TOKEN_FAILURES:
                # Token is permanently invalid — clear cached token and keep retrying
                # but at a slower rate to avoid hammering the auth server.
                # Don't exit: the user may re-enable wake from desktop which
                # will write a fresh refresh_token to the config file.
                logger.error(
                    f"Token refresh failed {consecutive_failures} times — "
                    "slowing poll to 5 min. Will resume on config update."
                )
                _cached_token = None
                time.sleep(300)  # 5 min backoff
            else:
                time.sleep(POLL_INTERVAL)
            continue

        # Poll for wake commands (also records daemon heartbeat server-side)
        if poll_wake(cloud_url, device_id, id_token):
            launch_desktop_app(app_path)
            # Wait extra time after launching to avoid rapid re-wake
            time.sleep(60)
            consecutive_failures = 0
        else:
            consecutive_failures = 0

        time.sleep(POLL_INTERVAL)

    logger.info("Wake daemon stopped")


if __name__ == "__main__":
    main()
