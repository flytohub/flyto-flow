"""In-process registry refresh for the already installed local core."""

import asyncio
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Callable, Dict, Optional, Set


class ModuleReloader:
    def __init__(self):
        self._listeners: Set[Callable] = set()
        self._lock = asyncio.Lock()
        self._version_info: Dict[str, Any] = {
            "version": self.get_installed_version(),
            "updated_at": None,
            "module_count": 0,
            "composite_count": 0,
        }

    @property
    def version_info(self) -> Dict[str, Any]:
        return dict(self._version_info)

    def add_listener(self, callback: Callable) -> None:
        self._listeners.add(callback)

    def remove_listener(self, callback: Callable) -> None:
        self._listeners.discard(callback)

    def get_installed_version(self) -> Optional[str]:
        try:
            return version("flyto-core")
        except PackageNotFoundError:
            return None

    async def reload(self, force: bool = False) -> Dict[str, Any]:
        del force
        async with self._lock:
            from services.infra.module_scanner import ModuleScanner

            scan = ModuleScanner().scan_modules()
            self._version_info.update(
                {
                    "version": self.get_installed_version(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "module_count": int(scan.get("count", 0)),
                    "composite_count": int(scan.get("composite_count", 0)),
                }
            )
            for callback in tuple(self._listeners):
                result = callback(self._version_info)
                if asyncio.iscoroutine(result):
                    await result
            return {
                "success": True,
                "version": self._version_info["version"],
                "modules": {
                    "atomic": self._version_info["module_count"],
                    "composite": self._version_info["composite_count"],
                },
            }


_reloader: Optional[ModuleReloader] = None


def get_module_reloader() -> ModuleReloader:
    global _reloader
    if _reloader is None:
        _reloader = ModuleReloader()
    return _reloader
