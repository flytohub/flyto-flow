"""
Core Plugin System API (Open Core Architecture)

Handles:
- List loaded module plugins
- Registry snapshot for version binding
- Registry refresh after install/upgrade
- Individual plugin update
"""
import sys
import subprocess
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from gateway.auth import get_admin_user
from gateway.providers.base import UserInfo

logger = logging.getLogger(__name__)

router = APIRouter()


class PluginStatus(BaseModel):
    """Plugin status information"""
    name: str
    version: str
    module_count: int
    loaded_at: str
    entry_point: str


class PluginsResponse(BaseModel):
    """Response for plugins list"""
    plugins: list[PluginStatus]
    total_modules: int
    registry_version: str


class RegistrySnapshotResponse(BaseModel):
    """Registry snapshot for execution version binding"""
    registry_version: str
    plugins: dict[str, str]
    module_count: int
    modules_hash: str
    created_at: str


class RefreshResult(BaseModel):
    """Result of registry refresh"""
    ok: bool
    message: str
    plugins_loaded: int
    modules_count: int


class UpdateResult(BaseModel):
    """Update operation result"""
    ok: bool
    message: str
    from_version: str | None
    to_version: str | None


def _get_module_registry():
    """Get ModuleRegistry from the installed flyto-core package."""
    try:
        from core.modules.registry import ModuleRegistry
        return ModuleRegistry
    except ImportError:
        return None


async def reload_core_modules():
    """
    Reload flyto-core modules after update.

    Uses ModuleRegistry.refresh() to re-discover all plugins.
    Note: This does not reload already-imported Python modules.
    For true hot-reload, worker processes should be restarted.
    """
    logger.info("Reloading core modules after update...")

    try:
        # Use the new plugin discovery refresh
        ModuleRegistry = _get_module_registry()
        if ModuleRegistry:
            plugins = ModuleRegistry.refresh()
            modules_count = ModuleRegistry.module_count()
            logger.info(f"Registry refreshed: {len(plugins)} plugins, {modules_count} modules")
        else:
            logger.warning("ModuleRegistry not available, skipping refresh")

        # Trigger module scanner if available (for UI metadata)
        try:
            from src.ui.web.backend.services.infra.module_scanner import ModuleScanner
            scanner = ModuleScanner()
            result = scanner.scan_modules()
            logger.info(f"Rescanned modules for UI: {result.get('count', 0)} modules found")
        except Exception as e:
            logger.warning(f"Could not rescan modules for UI: {e}")

    except Exception as e:
        logger.error(f"Error reloading modules: {e}")


@router.get("/plugins", response_model=PluginsResponse)
async def get_plugins():
    """
    Get all loaded module plugins.

    Returns information about all discovered plugins (community, pro, etc.)
    including version, module count, and load time.
    """
    ModuleRegistry = _get_module_registry()
    if not ModuleRegistry:
        raise HTTPException(
            status_code=503,
            detail="flyto-core not installed"
        )

    try:
        # Ensure plugins are discovered
        ModuleRegistry.discover_plugins()

        plugins = ModuleRegistry.get_plugins()
        plugin_list = [
            PluginStatus(
                name=info.name,
                version=info.version,
                module_count=info.module_count,
                loaded_at=info.loaded_at.isoformat(),
                entry_point=info.entry_point
            )
            for info in plugins.values()
        ]

        # Get registry version
        from core.modules.registry import REGISTRY_VERSION

        return PluginsResponse(
            plugins=plugin_list,
            total_modules=ModuleRegistry.module_count(),
            registry_version=REGISTRY_VERSION
        )

    except Exception as e:
        logger.error(f"Error getting plugins: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting plugins: {str(e)}"
        )


@router.get("/registry/snapshot", response_model=RegistrySnapshotResponse)
async def get_registry_snapshot():
    """
    Get a snapshot of current registry state.

    Used for execution version binding - each workflow execution
    should record this snapshot to ensure checkpoint/resume
    uses the same module versions.
    """
    ModuleRegistry = _get_module_registry()
    if not ModuleRegistry:
        raise HTTPException(
            status_code=503,
            detail="flyto-core not installed"
        )

    try:
        snapshot = ModuleRegistry.get_snapshot()
        return RegistrySnapshotResponse(
            registry_version=snapshot.registry_version,
            plugins=snapshot.plugins,
            module_count=snapshot.module_count,
            modules_hash=snapshot.modules_hash,
            created_at=snapshot.created_at.isoformat()
        )

    except Exception as e:
        logger.error(f"Error getting registry snapshot: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting snapshot: {str(e)}"
        )


@router.post("/registry/refresh", response_model=RefreshResult)
async def refresh_registry(
    admin: UserInfo = Depends(get_admin_user),
):
    """
    Refresh the module registry by re-discovering all plugins.

    This is used after pip install/upgrade to reload modules.
    Note: For true hot-reload, worker processes should be restarted.

    REQUIRES ADMIN - Only administrators can refresh registry.
    """
    logger.info(f"Registry refresh requested by admin: {admin.email}")

    ModuleRegistry = _get_module_registry()
    if not ModuleRegistry:
        return RefreshResult(
            ok=False,
            message="flyto-core not installed",
            plugins_loaded=0,
            modules_count=0
        )

    try:
        # Refresh registry (clears and re-discovers)
        plugins = ModuleRegistry.refresh()

        modules_count = ModuleRegistry.module_count()
        plugins_count = len(plugins)

        logger.info(f"Registry refreshed: {plugins_count} plugins, {modules_count} modules")

        return RefreshResult(
            ok=True,
            message=f"Registry refreshed: {plugins_count} plugins, {modules_count} modules",
            plugins_loaded=plugins_count,
            modules_count=modules_count
        )

    except Exception as e:
        logger.error(f"Error refreshing registry: {e}")
        return RefreshResult(
            ok=False,
            message=f"Refresh error: {str(e)}",
            plugins_loaded=0,
            modules_count=0
        )


@router.post("/plugins/{plugin_name}/update", response_model=UpdateResult)
def _get_pip_version(package_name: str) -> Optional[str]:
    """Get installed version of a pip package. Returns None if not found."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':', 1)[1].strip()
    except Exception:
        pass
    return None


# Map plugin names to PyPI packages
_PLUGIN_PACKAGES = {
    "community": "flyto-core",
    "pro": "flyto-modules-pro",
}


async def update_plugin(
    plugin_name: str,
    admin: UserInfo = Depends(get_admin_user),
):
    """
    Update a specific plugin package from PyPI.

    Plugin names:
    - community: flyto-core (open source modules)
    - pro: flyto-modules-pro (commercial modules)

    REQUIRES ADMIN - Only administrators can update packages.
    """
    logger.info(f"Plugin update requested by admin: {admin.email}, plugin: {plugin_name}")

    package_name = _PLUGIN_PACKAGES.get(plugin_name)
    if not package_name:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown plugin: {plugin_name}. Valid plugins: {list(_PLUGIN_PACKAGES.keys())}"
        )

    old_version = _get_pip_version(package_name)

    try:
        logger.info(f"Updating {package_name} from PyPI...")

        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", package_name],
            capture_output=True, text=True, timeout=120,
        )

        if result.returncode != 0:
            logger.error(f"pip upgrade failed: {result.stderr}")
            return UpdateResult(
                ok=False,
                message=f"Update failed: {result.stderr[:200]}",
                from_version=old_version, to_version=None,
            )

        new_version = _get_pip_version(package_name)

        # Refresh registry to pick up new modules
        ModuleRegistry = _get_module_registry()
        if ModuleRegistry:
            ModuleRegistry.refresh()

        if old_version == new_version:
            return UpdateResult(
                ok=True,
                message=f"{plugin_name} already on latest version: {new_version}",
                from_version=old_version, to_version=new_version,
            )

        logger.info(f"Updated {plugin_name}: {old_version} -> {new_version}")
        return UpdateResult(
            ok=True,
            message=f"Updated {plugin_name}: {old_version} -> {new_version}",
            from_version=old_version, to_version=new_version,
        )

    except subprocess.TimeoutExpired:
        return UpdateResult(
            ok=False, message="Update timed out. Please try again.",
            from_version=old_version, to_version=None,
        )
    except Exception as e:
        logger.error(f"Update error: {e}")
        return UpdateResult(
            ok=False, message=f"Update error: {str(e)}",
            from_version=old_version, to_version=None,
        )
