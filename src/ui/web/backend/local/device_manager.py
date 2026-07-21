"""
Device Manager — auto-registration loop, device ID/name helpers, token capture.

Captures the first Bearer token from authenticated requests, registers
this machine to the Cloud API, then sends periodic heartbeats so the
device appears as "online" in the mobile app.
"""
import asyncio
import hashlib
import logging
import os
import platform
import socket

from config.constants import APP_VERSION

logger = logging.getLogger(__name__)

# Shared token state — captured from authenticated requests
_captured_token: str | None = None
_device_tasks_started: bool = False
_device_register_running: bool = False


def get_captured_token() -> str | None:
    """Get the currently captured Bearer token."""
    return _captured_token


def set_captured_token(token: str) -> None:
    """Set the captured Bearer token (called from middleware)."""
    global _captured_token
    _captured_token = token


def get_device_tasks_started() -> bool:
    """Whether device/poll tasks have been launched."""
    return _device_tasks_started


def set_device_tasks_started(value: bool) -> None:
    """Mark device/poll tasks as started."""
    global _device_tasks_started
    _device_tasks_started = value


def _is_cloud_run() -> bool:
    """Check if running on Cloud Run (K_SERVICE is set by Cloud Run)."""
    return bool(os.environ.get("K_SERVICE"))


def get_device_id() -> str:
    """Generate a stable device ID based on hostname + platform."""
    if _is_cloud_run():
        # Cloud Run workers share the same logical identity
        service = os.environ.get("K_SERVICE", "cloud-worker")
        raw = f"cloud:{service}"
    else:
        raw = f"{socket.gethostname()}:{platform.system()}:{platform.machine()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_device_name() -> str:
    """Human-readable device name."""
    if _is_cloud_run():
        service = os.environ.get("K_SERVICE", "cloud-worker")
        return f"Cloud ({service})"
    return f"{socket.gethostname()} ({platform.system()})"


def get_local_url() -> str | None:
    """Get the local network URL for this device's API server.

    Uses the configured port (default 9000) and the machine's LAN IP.
    """
    port = os.environ.get("PORT", "9000")
    try:
        # Connect to a public DNS to discover our LAN IP (no data is sent)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return f"http://{ip}:{port}"
    except Exception:
        return None


async def device_auto_register_loop(get_proxy_client):
    """Wait for a Bearer token, then register + heartbeat.

    Args:
        get_proxy_client: Async callable that returns an httpx.AsyncClient.
    """
    global _captured_token, _device_register_running
    if _device_register_running:
        return  # Already running from another caller
    _device_register_running = True

    # Wait until we capture a token from an authenticated request
    while _captured_token is None:
        await asyncio.sleep(0.5)

    device_id = get_device_id()
    if _is_cloud_run():
        _plat = "cloud"
    else:
        _plat = platform.system().lower()
        if _plat == "windows":
            _plat = "win32"

    try:
        client = await get_proxy_client()
        resp = await client.post(
            "/api/devices/register",
            json={
                "name": get_device_name(),
                "workspace_id": "default",
                "platform": _plat,
                "version": APP_VERSION,
                "device_id": device_id,
            },
            headers={"Authorization": f"Bearer {_captured_token}"},
            timeout=15,
        )
        if resp.status_code < 300:
            logger.info(f"Device auto-registered: {device_id} ({get_device_name()})")
        else:
            logger.warning(f"Device registration failed: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"Device auto-registration failed: {e}")

    # Heartbeat loop — always use latest _captured_token (refreshed by middleware)
    while True:
        await asyncio.sleep(30)
        try:
            client = await get_proxy_client()
            local_url = get_local_url()
            resp = await client.post(
                f"/api/devices/{device_id}/heartbeat",
                json={"local_url": local_url} if local_url else None,
                headers={"Authorization": f"Bearer {_captured_token}"},
                timeout=10,
            )
            if resp.status_code == 401:
                logger.warning("Heartbeat 401 — token expired, waiting for refresh")
        except Exception:
            pass
