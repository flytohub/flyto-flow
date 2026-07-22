"""Local flyto-core health and version endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version as package_version

from fastapi import APIRouter
from pydantic import BaseModel

from local.core_wheel import read_active_core


router = APIRouter()


class CoreStatus(BaseModel):
    installed: bool
    installed_version: str | None
    source: str
    latest_version: None = None
    update_available: bool = False
    last_check: str


def get_installed_version() -> str | None:
    active = read_active_core()
    if active:
        return active.version
    try:
        return package_version("flyto-core")
    except PackageNotFoundError:
        return None


@router.get("/health")
async def core_health():
    installed = get_installed_version()
    return {
        "ok": installed is not None,
        "status": "healthy" if installed else "missing",
        "service": "flyto-core",
        "version": installed,
    }


@router.get("/version")
async def core_version():
    active = read_active_core()
    installed = get_installed_version()
    return {
        "ok": installed is not None,
        "version": installed or "not installed",
        "package": "flyto-core",
        "source": "offline-wheel" if active else "image",
        "sha256": active.sha256 if active else None,
    }


@router.get("/status", response_model=CoreStatus)
async def get_core_status():
    """Return local state only; CE never checks PyPI for a newer release."""
    active = read_active_core()
    installed = get_installed_version()
    return CoreStatus(
        installed=installed is not None,
        installed_version=installed,
        source="offline-wheel" if active else "image",
        last_check=datetime.now(timezone.utc).isoformat(),
    )
