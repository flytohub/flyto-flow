"""
Hot Updater Module Reload

Hot-reload modules after core update.
Adapted for wheel layout: core/ is at root of version dir, not under src/.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Tuple

from services.infra.updater.constants import utc_now

logger = logging.getLogger(__name__)


async def reload_modules(current_path: Optional[Path]) -> Tuple[int, int]:
    """
    Hot-reload modules after update.

    Wheel layout: ~/.flyto/core/{version}/core/
    The version dir itself should be on sys.path so `import core.modules` works.

    Args:
        current_path: Path to current version directory (e.g., ~/.flyto/core/1.2.3/)

    Returns:
        Tuple of (module_count, composite_count)
    """
    logger.info("Reloading flyto-core modules...")

    if not current_path:
        return 0, 0

    # Wheel layout: core/ is directly under the version dir
    core_pkg = current_path / "core"
    if not core_pkg.exists():
        # Fallback: try src/ layout (legacy GitHub source installs)
        src_path = current_path / "src"
        if src_path.exists():
            path_to_add = str(src_path)
        else:
            logger.warning("No core package found in %s", current_path)
            return 0, 0
    else:
        # Wheel layout: add version dir to sys.path so `import core` resolves
        path_to_add = str(current_path)

    # Clear cached core modules from sys.modules so fresh imports pick up new version
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key == 'core' or key.startswith('core.')
    ]
    for key in modules_to_remove:
        del sys.modules[key]

    # Update sys.path
    if path_to_add not in sys.path:
        sys.path.insert(0, path_to_add)

    # Reset RegistryLoader singleton so it re-imports from the new version
    from services.registry_loader import get_registry_loader
    loader = get_registry_loader()
    loader._initialized = False
    loader._module_registry = None
    loader._composite_registry = None
    loader._connection_validator = None

    # Scan modules — RegistryLoader will import fresh core.modules.atomic,
    # which triggers register_all() on the new ModuleRegistry class.
    # No need for ModuleRegistry.clear(): clearing sys.modules already ensures
    # a fresh class with empty _modules dict.
    module_count = 0
    composite_count = 0
    try:
        from services.infra.module_scanner import ModuleScanner
        scanner = ModuleScanner(core_path=str(current_path))
        result = scanner.scan_modules()

        module_count = result.get('count', 0)
        composite_count = result.get('composite_count', 0)
        logger.info("Reloaded %d modules", module_count)

    except Exception as e:
        logger.error("Error reloading modules: %s", e)

    return module_count, composite_count


async def notify_frontend_update(
    current_version: Optional[str],
    module_count: int,
    composite_count: int
) -> None:
    """
    Broadcast update notification to connected frontend clients.

    Args:
        current_version: Current version string
        module_count: Number of modules loaded
        composite_count: Number of composite modules loaded
    """
    try:
        from websocket.module_sync import get_module_sync_manager

        manager = get_module_sync_manager()
        await manager.broadcast_module_update({
            "version": current_version,
            "updated_at": utc_now().isoformat(),
            "module_count": module_count,
            "composite_count": composite_count
        })
        logger.info("Notified frontend of module update")
    except Exception as e:
        logger.warning("Failed to notify frontend: %s", e)


async def notify_frontend_version_update(version: str) -> None:
    """
    Broadcast frontend version update notification via WebSocket.

    Tells connected clients to reload to pick up the new frontend build.

    Args:
        version: New frontend version string
    """
    try:
        from websocket.module_sync import get_module_sync_manager

        manager = get_module_sync_manager()
        await manager.broadcast({
            "type": "frontend_updated",
            "version": version,
            "action": "reload",
        })
        logger.info("Notified frontend of version update: %s", version)
    except Exception as e:
        logger.warning("Failed to notify frontend of version update: %s", e)
