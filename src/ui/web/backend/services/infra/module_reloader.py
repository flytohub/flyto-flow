"""
Module Hot Reload Service

Provides hot reload capability for flyto-core modules without backend restart.

All environments use PyPI package:
- Online: pip install --upgrade flyto-core
- Offline: pip install flyto_core-x.x.x.whl

Import path: core.modules (unified, no src.core.modules)
"""
import asyncio
from datetime import datetime, timezone
import importlib
import logging
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class ModuleReloader:
    """
    Handles hot reloading of flyto-core modules.

    Features:
    - Clear Python module cache
    - Re-import registries
    - Version tracking
    - Broadcast to connected clients

    Update methods:
    - pip_upgrade(): Online update from PyPI
    - reload(): Reload after pip install (online or .whl)
    """

    def __init__(self):
        """Initialize reloader with default version info and reload settings."""
        self._version_info: Dict[str, Any] = {
            "version": "1.0.0",
            "updated_at": None,
            "module_count": 0,
            "composite_count": 0,
        }
        self._listeners: Set[Callable] = set()
        self._reload_lock = asyncio.Lock()
        self._last_reload: Optional[datetime] = None
        self._min_reload_interval = 60  # seconds

    @property
    def version_info(self) -> Dict[str, Any]:
        """Get a copy of the current version info."""
        return self._version_info.copy()

    def add_listener(self, callback: Callable):
        """Add a callback to be notified on reload."""
        self._listeners.add(callback)

    def remove_listener(self, callback: Callable):
        """Remove a reload listener."""
        self._listeners.discard(callback)

    def get_installed_version(self) -> Optional[str]:
        """Get installed flyto-core version via pip."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", "flyto-core"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        return line.split(':', 1)[1].strip()
            return None
        except Exception as e:
            logger.error(f"Error getting installed version: {e}")
            return None

    async def pip_upgrade(self) -> Dict[str, Any]:
        """
        Upgrade flyto-core via pip from PyPI.

        Returns:
            Dict with success status and version info
        """
        old_version = self.get_installed_version()

        try:
            logger.info("Upgrading flyto-core via pip...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "flyto-core"],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr[:500] if result.stderr else "pip upgrade failed",
                    "old_version": old_version
                }

            new_version = self.get_installed_version()
            logger.info(f"Upgraded flyto-core: {old_version} -> {new_version}")

            return {
                "success": True,
                "old_version": old_version,
                "new_version": new_version,
                "changed": old_version != new_version
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "pip upgrade timed out after 120 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _clear_module_cache(self) -> List[str]:
        """
        Clear Python module cache for flyto-core modules.

        Clears: core.modules.* (pip-installed package)
        """
        modules_to_clear = [
            key for key in list(sys.modules.keys())
            if key.startswith("core.modules") or key.startswith("core.") or key == "core"
        ]

        for module_name in modules_to_clear:
            del sys.modules[module_name]

        logger.info(f"Cleared {len(modules_to_clear)} cached modules")
        return modules_to_clear

    def _reload_registries(self) -> Dict[str, int]:
        """
        Reload module registries from pip-installed flyto-core.

        Import path: core.modules (unified)

        Note: _clear_module_cache() must be called BEFORE this method.
        Clearing sys.modules ensures fresh imports which create new Registry
        classes with empty state. No need for explicit clear() — the old
        class (and its _modules dict) is garbage-collected.
        """
        counts = {"atomic": 0, "composite": 0}

        # Reset RegistryLoader singleton so it re-imports from fresh modules
        from services.registry_loader import get_registry_loader
        loader = get_registry_loader()
        loader._initialized = False
        loader._module_registry = None
        loader._composite_registry = None
        loader._connection_validator = None

        # Reload atomic modules via RegistryLoader (triggers fresh import chain)
        try:
            from services.infra.module_scanner import ModuleScanner
            scanner = ModuleScanner()
            result = scanner.scan_modules()
            counts["atomic"] = result.get('count', 0)
            logger.info(f"Loaded {counts['atomic']} atomic modules")
        except ImportError as e:
            logger.error(f"Failed to import core.modules: {e}")
            logger.error("Make sure flyto-core is installed: pip install flyto-core")
        except Exception as e:
            logger.error(f"Failed to reload atomic modules: {e}")

        # Reload composite modules
        try:
            from core.modules.composite import CompositeRegistry
            counts["composite"] = CompositeRegistry.module_count()
            logger.info(f"Loaded {counts['composite']} composite modules")
        except ImportError:
            logger.debug("Composite registry not available")
        except Exception as e:
            logger.error(f"Failed to reload composite modules: {e}")

        return counts

    async def reload(self, force: bool = False) -> Dict[str, Any]:
        """
        Reload modules from pip-installed flyto-core.

        Call this after:
        - pip install --upgrade flyto-core (online)
        - pip install flyto_core-x.x.x.whl (offline)

        Args:
            force: Skip rate limiting

        Returns:
            Reload result with module counts
        """
        now = _utc_now()

        # Rate limiting
        if not force and self._last_reload:
            elapsed = (now - self._last_reload).total_seconds()
            if elapsed < self._min_reload_interval:
                return {
                    "success": False,
                    "error": f"Rate limited. Try again in {self._min_reload_interval - elapsed:.0f}s"
                }

        async with self._reload_lock:
            result = {
                "success": True,
                "modules": {"atomic": 0, "composite": 0},
                "cleared": 0,
                "version": None,
                "timestamp": now.isoformat()
            }

            try:
                # 1. Clear module cache
                cleared = self._clear_module_cache()
                result["cleared"] = len(cleared)

                # 2. Reload registries
                counts = self._reload_registries()
                result["modules"] = counts

                # 3. Update version info
                installed_version = self.get_installed_version()
                self._version_info.update({
                    "version": installed_version or f"1.0.{counts['atomic'] + counts['composite']}",
                    "updated_at": now.isoformat(),
                    "module_count": counts["atomic"],
                    "composite_count": counts["composite"],
                })
                result["version"] = self._version_info["version"]

                self._last_reload = now

                # 4. Notify listeners
                await self._notify_listeners()

                logger.info(
                    f"Hot reload complete: {counts['atomic']} atomic, "
                    f"{counts['composite']} composite modules"
                )

            except Exception as e:
                logger.exception("Hot reload failed")
                result["success"] = False
                result["error"] = str(e)

            return result

    async def upgrade_and_reload(self) -> Dict[str, Any]:
        """
        Full upgrade flow:
        1. pip install --upgrade flyto-core
        2. Clear module cache
        3. Reload registries

        This is the recommended method for online updates.
        """
        result = {
            "success": True,
            "pip": None,
            "reload": None
        }

        # 1. Upgrade via pip
        pip_result = await self.pip_upgrade()
        result["pip"] = pip_result

        if not pip_result["success"]:
            result["success"] = False
            result["error"] = pip_result.get("error", "pip upgrade failed")
            return result

        # 2. Reload modules
        reload_result = await self.reload(force=True)
        result["reload"] = reload_result

        if not reload_result["success"]:
            result["success"] = False
            result["error"] = reload_result.get("error", "reload failed")

        return result

    async def _notify_listeners(self):
        """Notify all registered listeners of reload."""
        for callback in self._listeners:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self._version_info)
                else:
                    callback(self._version_info)
            except Exception as e:
                logger.error(f"Listener callback failed: {e}")


# Singleton instance
_reloader: Optional[ModuleReloader] = None


def get_module_reloader() -> ModuleReloader:
    """Get singleton ModuleReloader instance."""
    global _reloader
    if _reloader is None:
        _reloader = ModuleReloader()
    return _reloader
