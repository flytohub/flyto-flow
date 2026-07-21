"""
Hot Updater Service

Main HotUpdater class that orchestrates core + frontend + app updates.
"""

import asyncio
import shutil
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.infra.updater.config import load_config, save_config
from services.infra.updater.constants import utc_now
from services.infra.updater.download import download_version, install_symlink, resolve_current_path
from services.infra.updater.frontend import FrontendUpdater
from services.infra.updater.models import CoreVersion, FrontendVersion, UpdateStatus
from services.infra.updater.reload import notify_frontend_update, notify_frontend_version_update, reload_modules
from services.infra.updater.version import check_for_updates, compare_versions

logger = logging.getLogger(__name__)


class HotUpdater:
    """
    Manages hot updates for flyto desktop app.

    Three-layer strategy:
    - Core (flyto-core): PyPI wheel -> ~/.flyto/core/{version}/
    - Frontend: GitHub release asset -> ~/.flyto/frontend/dist/
    - Backend: Cloud API proxy (always up to date); only notifies of new app versions
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize updater."""
        self.base_dir = base_dir or Path.home() / ".flyto"
        self.core_dir = self.base_dir / "core"
        self.cache_dir = self.base_dir / "cache"
        self.config_path = self.base_dir / "config.json"

        # Ensure directories exist
        self.core_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load config
        self._config = load_config(self.config_path)

        # Frontend updater
        self._frontend_updater = FrontendUpdater(self.base_dir)

        # Background update task
        self._update_task: Optional[asyncio.Task] = None
        self._running = False

    def _save_config(self):
        """Save user configuration."""
        save_config(self.config_path, self._config)

    # =========================================================================
    # Core version management
    # =========================================================================

    @property
    def current_version(self) -> Optional[str]:
        """Get currently installed core version."""
        current_path = resolve_current_path(self.core_dir)
        if current_path:
            return current_path.name
        return self._config.get("current_version")

    @property
    def current_path(self) -> Optional[Path]:
        """Get path to current flyto-core installation."""
        return resolve_current_path(self.core_dir)

    def get_installed_versions(self) -> List[str]:
        """List all installed core versions."""
        versions = []
        for item in self.core_dir.iterdir():
            if item.is_dir() and item.name not in ("current",):
                # Check it looks like a version dir (has core/ inside)
                if (item / "core").exists():
                    versions.append(item.name)
        return sorted(versions, key=lambda v: [int(x) for x in v.lstrip('v').split('.')[:3] if x.isdigit()], reverse=True)

    # =========================================================================
    # Frontend version management
    # =========================================================================

    @property
    def frontend_path(self) -> Optional[Path]:
        """Get path to hot-updated frontend dist, if available."""
        return self._frontend_updater.frontend_path

    @property
    def frontend_version(self) -> Optional[str]:
        """Get currently installed frontend version."""
        return self._frontend_updater.current_version

    # =========================================================================
    # Update operations
    # =========================================================================

    async def check_for_core_updates(self, force: bool = False) -> Optional[CoreVersion]:
        """Check PyPI for new core releases."""
        result = await check_for_updates(
            self._config, self.current_version, force
        )

        if result or force:
            self._config["last_check"] = utc_now().isoformat()
            self._save_config()

        return result

    async def check_for_frontend_updates(self, app_version: str) -> Optional[FrontendVersion]:
        """Check GitHub for new frontend releases."""
        return await self._frontend_updater.check_for_updates(app_version)

    async def download_core_version(self, version: CoreVersion) -> Optional[Path]:
        """Download a specific core version from PyPI."""
        return await download_version(version, self.core_dir, self.cache_dir)

    async def install_core_version(self, version: str) -> bool:
        """Install (activate) a downloaded core version."""
        if not install_symlink(version, self.core_dir):
            return False

        self._config["current_version"] = version
        self._save_config()

        module_count, composite_count = await reload_modules(self.current_path)

        await notify_frontend_update(
            self.current_version, module_count, composite_count
        )

        logger.info("Installed flyto-core %s", version)
        return True

    async def update_core(self, force: bool = False) -> Dict[str, Any]:
        """Check for core updates and install if available."""
        result = {
            "checked": True,
            "updated": False,
            "from_version": self.current_version,
            "to_version": None,
            "error": None
        }

        try:
            new_version = await self.check_for_core_updates(force=force)

            if not new_version:
                return result

            download_path = await self.download_core_version(new_version)
            if not download_path:
                result["error"] = "Download failed"
                return result

            if await self.install_core_version(new_version.version):
                result["updated"] = True
                result["to_version"] = new_version.version
            else:
                result["error"] = "Installation failed"

            return result

        except Exception as e:
            result["error"] = str(e)
            return result

    async def update_frontend(self, app_version: str) -> Dict[str, Any]:
        """Check for frontend updates and install if available."""
        result = {
            "checked": True,
            "updated": False,
            "from_version": self.frontend_version,
            "to_version": None,
            "error": None
        }

        try:
            new_version = await self.check_for_frontend_updates(app_version)
            if not new_version:
                return result

            if await self._frontend_updater.download_and_install(new_version):
                result["updated"] = True
                result["to_version"] = new_version.version

                # Notify connected frontends to reload
                await notify_frontend_version_update(new_version.version)
            else:
                result["error"] = "Frontend download failed"

            return result

        except Exception as e:
            result["error"] = str(e)
            return result

    async def update_all(self, app_version: str, force: bool = False) -> Dict[str, Any]:
        """Run all update checks (core + frontend)."""
        core_result = await self.update_core(force=force)
        frontend_result = await self.update_frontend(app_version)
        return {
            "core": core_result,
            "frontend": frontend_result,
        }

    # =========================================================================
    # Rollback
    # =========================================================================

    async def rollback(self, version: Optional[str] = None) -> bool:
        """Rollback to a previous core version."""
        versions = self.get_installed_versions()
        current = self.current_version

        if not versions:
            logger.error("No versions installed")
            return False

        if version:
            if version not in versions:
                logger.error("Version %s not installed", version)
                return False
            target = version
        else:
            try:
                current_idx = versions.index(current) if current else -1
                if current_idx >= len(versions) - 1:
                    logger.error("No previous version available")
                    return False
                target = versions[current_idx + 1]
            except ValueError:
                target = versions[0]

        logger.info("Rolling back from %s to %s", current, target)
        return await self.install_core_version(target)

    # =========================================================================
    # Background updates
    # =========================================================================

    async def start_background_updates(self):
        """Start background update checking."""
        if self._running:
            return

        self._running = True
        self._update_task = asyncio.create_task(self._background_update_loop())
        logger.info("Started background update checker")

    async def stop_background_updates(self):
        """Stop background update checking."""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped background update checker")

    async def _background_update_loop(self):
        """Background loop: check core (PyPI) + frontend (GitHub) every hour.

        Delays first check by 120 seconds to avoid updating during startup.
        """
        STARTUP_UPDATE_DELAY = 120  # 2 minutes

        # Delay first check to let the app stabilize after startup
        await asyncio.sleep(STARTUP_UPDATE_DELAY)

        first_run = True
        while self._running:
            try:
                if self._config.get("auto_update", True):
                    from config.constants import APP_VERSION
                    force = first_run
                    first_run = False
                    await self.update_all(app_version=APP_VERSION, force=force)
                    await self.cleanup_old_versions(keep=3)

                interval = self._config.get("check_interval_hours", 1) * 3600
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in background update: %s", e)
                await asyncio.sleep(60)

    # =========================================================================
    # Status & config
    # =========================================================================

    def get_status(self) -> UpdateStatus:
        """Get current update status for all components."""
        from config.constants import APP_VERSION
        return UpdateStatus(
            core_current=self.current_version or "not installed",
            core_latest=self._config.get("latest_version", "unknown"),
            core_update_available=False,
            frontend_current=self.frontend_version or "unknown",
            frontend_latest="unknown",
            frontend_update_available=False,
            app_version=APP_VERSION,
            app_update_available=False,
            last_check=self._config.get("last_check", "never"),
            auto_update=self._config.get("auto_update", True),
        )

    def set_auto_update(self, enabled: bool):
        """Enable/disable auto-updates."""
        self._config["auto_update"] = enabled
        self._save_config()

    def pin_version(self, version: Optional[str]):
        """Pin to a specific version (won't auto-update past it)."""
        self._config["pinned_version"] = version
        self._save_config()

    async def cleanup_old_versions(self, keep: int = 3):
        """Remove old core versions, keeping the most recent ones."""
        versions = self.get_installed_versions()
        current = self.current_version

        versions_to_keep = {current} if current else set()
        for v in versions[:keep]:
            versions_to_keep.add(v)

        for version in versions:
            if version not in versions_to_keep:
                version_dir = self.core_dir / version
                try:
                    shutil.rmtree(version_dir)
                    logger.info("Removed old version: %s", version)
                except Exception as e:
                    logger.error("Failed to remove %s: %s", version, e)


# Backward-compatible alias
CoreUpdater = HotUpdater

# Singleton instance
_updater: Optional[HotUpdater] = None


def get_core_updater() -> HotUpdater:
    """Get or create HotUpdater singleton."""
    global _updater
    if _updater is None:
        _updater = HotUpdater()
    return _updater


# Alias for backward compatibility
get_hot_updater = get_core_updater


async def init_core_updater():
    """Initialize and start the hot updater."""
    updater = get_core_updater()

    if not updater.current_version:
        logger.info("First run - downloading latest flyto-core...")
        await updater.update_core(force=True)

    await updater.start_background_updates()
    return updater
