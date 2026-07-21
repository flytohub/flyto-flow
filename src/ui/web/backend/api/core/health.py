"""
Core Health & Version Endpoints

Handles:
- Health check
- Installed version query
- Core status (installed vs latest)
"""
import sys
import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from config.settings import get_settings
from services.infra.updater.constants import utc_now
from services.infra.updater.version import compare_versions, check_pypi_latest

logger = logging.getLogger(__name__)

router = APIRouter()


# Re-export for backward compatibility (used by main_local.py, main.py)
get_pypi_latest_version = check_pypi_latest


class CoreStatus(BaseModel):
    """Core package status"""
    installed: bool
    installed_version: Optional[str]
    latest_version: Optional[str]
    update_available: bool
    last_check: Optional[str]


def get_installed_version() -> Optional[str]:
    """Get installed flyto-core version (hot-updated or pip)."""
    # Packaged mode: prefer hot-updated version
    if getattr(sys, 'frozen', False):
        try:
            from services.infra.updater import get_core_updater
            hot_version = get_core_updater().current_version
            if hot_version:
                return hot_version
        except Exception:
            pass

    # Dev mode / fallback: read from pip-installed package
    try:
        from importlib.metadata import version as pkg_version
        return pkg_version("flyto-core")
    except Exception:
        pass

    return None


@router.get("/health")
async def core_health():
    """Health check endpoint for core service."""
    return {
        "ok": True,
        "status": "healthy",
        "service": "core",
        "version": "1.0.0",
    }


@router.get("/version")
async def core_version():
    """Get core package version information."""
    installed = get_installed_version()
    return {
        "ok": True,
        "version": installed or "not installed",
        "package": "flyto-core",
    }


@router.get("/status", response_model=CoreStatus)
async def get_core_status():
    """
    Get flyto-core package status.
    Returns installed version and latest PyPI version.

    In offline mode: Only returns installed version, skips PyPI check.
    """
    get_settings()
    installed_version = get_installed_version()

    latest_version = await get_pypi_latest_version()

    update_available = False
    if installed_version and latest_version:
        update_available = compare_versions(latest_version, installed_version) > 0

    return CoreStatus(
        installed=installed_version is not None,
        installed_version=installed_version,
        latest_version=latest_version,
        update_available=update_available,
        last_check=utc_now().isoformat()
    )
