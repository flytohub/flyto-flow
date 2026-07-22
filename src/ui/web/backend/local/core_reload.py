"""Reload an operator-imported flyto-core wheel from local disk."""

import sys
from pathlib import Path


async def reload_modules(current_path: Path) -> tuple[int, int]:
    core_package = current_path / "core"
    if not core_package.is_dir():
        raise ValueError("Imported wheel does not contain the core package")

    for name in [key for key in sys.modules if key == "core" or key.startswith("core.")]:
        del sys.modules[name]
    path_value = str(current_path)
    if path_value not in sys.path:
        sys.path.insert(0, path_value)

    from services.registry_loader import get_registry_loader

    loader = get_registry_loader()
    loader._initialized = False
    loader._module_registry = None
    loader._composite_registry = None
    loader._connection_validator = None

    from services.infra.module_scanner import ModuleScanner

    result = ModuleScanner(core_path=path_value).scan_modules()
    module_count = int(result.get("count", 0))
    composite_count = int(result.get("composite_count", 0))

    from websocket.module_sync import get_module_sync_manager

    await get_module_sync_manager().broadcast_module_update(
        {
            "type": "core_reloaded",
            "module_count": module_count,
            "composite_count": composite_count,
        }
    )
    return module_count, composite_count
