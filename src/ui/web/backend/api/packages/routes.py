"""
Route handlers for the Package Manager API.
"""

import asyncio
import logging
from typing import List

from fastapi import APIRouter, HTTPException

from services.infra.updater.version import compare_versions
from services.infra.updater.constants import utc_now

from .models import PackageStatus, PackageActionResult, AutoUpdateRequest
from .helpers import (
    SYSTEM_PACKAGES,
    _PACKAGES_BY_ID,
    _load_auto_update_settings,
    _save_auto_update_settings,
    _get_installed_version,
    _check_pypi_latest,
    _install_or_update_package,
    _remove_package_impl,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/packages", tags=["Packages"])


@router.get("/status", response_model=List[PackageStatus])
async def get_packages_status():
    """Get status of all system packages."""
    auto_update_settings = _load_auto_update_settings()
    now = utc_now().isoformat()

    # Gather installed versions (sync, fast)
    installed_versions = {}
    for pkg in SYSTEM_PACKAGES:
        installed_versions[pkg['id']] = _get_installed_version(pkg)

    # Gather latest versions from PyPI in parallel
    pypi_tasks = {}
    for pkg in SYSTEM_PACKAGES:
        if pkg.get('pypi_url'):
            pypi_tasks[pkg['id']] = _check_pypi_latest(pkg['pypi_url'])

    latest_versions = {}
    if pypi_tasks:
        results = await asyncio.gather(*pypi_tasks.values(), return_exceptions=True)
        for pkg_id, result in zip(pypi_tasks.keys(), results):
            if isinstance(result, Exception):
                latest_versions[pkg_id] = None
            else:
                latest_versions[pkg_id] = result

    # Build response
    statuses = []
    for pkg in SYSTEM_PACKAGES:
        installed = installed_versions.get(pkg['id'])
        latest = latest_versions.get(pkg['id'])

        update_available = False
        if installed and latest:
            update_available = compare_versions(latest, installed) > 0

        statuses.append(PackageStatus(
            id=pkg['id'],
            name=pkg['name'],
            description=pkg['description'],
            icon=pkg['icon'],
            color=pkg['color'],
            category=pkg['category'],
            removable=pkg['removable'],
            installed=installed is not None,
            installed_version=installed,
            latest_version=latest,
            update_available=update_available,
            auto_update=auto_update_settings.get(pkg['id'], False),
            last_check=now,
        ))

    return statuses


@router.post("/{package_id}/update", response_model=PackageActionResult)
async def update_package(package_id: str):
    """Update a specific package to latest version."""
    return await _install_or_update_package(package_id, upgrade=True)


@router.post("/{package_id}/install", response_model=PackageActionResult)
async def install_package(package_id: str):
    """Install a specific package."""
    pkg = _PACKAGES_BY_ID.get(package_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    if _get_installed_version(pkg) and package_id != 'chromium':
        return PackageActionResult(
            ok=False, message="Package is already installed", package_id=package_id,
        )

    return await _install_or_update_package(package_id, upgrade=False)


@router.delete("/{package_id}", response_model=PackageActionResult)
async def remove_package(package_id: str):
    """Remove a specific package (only if removable)."""
    return await _remove_package_impl(package_id)


@router.put("/{package_id}/auto-update")
async def set_auto_update(package_id: str, body: AutoUpdateRequest):
    """Enable or disable auto-update for a specific package."""
    if package_id not in _PACKAGES_BY_ID:
        raise HTTPException(status_code=404, detail="Package not found")

    settings = _load_auto_update_settings()
    settings[package_id] = body.enabled
    _save_auto_update_settings(settings)

    return {
        "ok": True,
        "package_id": package_id,
        "auto_update": body.enabled,
    }
