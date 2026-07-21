"""
Backward compatibility — imports from split modules.

All symbols previously in this file are re-exported so that
existing imports (tests, other modules) continue to work.
"""
from fastapi import APIRouter

from api.core.health import router as _health_router
from api.core.plugins import router as _plugins_router
from api.core.updater import router as _updater_router

# Compose the same router that __init__.py builds, so that
# ``from api.core.routes import router`` keeps working.
router = APIRouter(prefix="/core", tags=["Core"])
router.include_router(_health_router)
router.include_router(_plugins_router)
router.include_router(_updater_router)

# Health & version
from api.core.health import (  # noqa: F401
    CoreStatus,
    get_installed_version,
    get_pypi_latest_version,
    core_health,
    core_version,
    get_core_status,
)

# Plugins & registry
from api.core.plugins import (  # noqa: F401
    PluginStatus,
    PluginsResponse,
    RegistrySnapshotResponse,
    RefreshResult,
    _get_module_registry,
    reload_core_modules,
    get_plugins,
    get_registry_snapshot,
    refresh_registry,
    update_plugin,
)

# Updater (upload, install, update)
from api.core.updater import (  # noqa: F401
    SAFE_FILENAME_PATTERN,
    UpdateResult,
    _validate_safe_filename,
    update_core_online,
    upload_core_package,
    install_base_package,
)
