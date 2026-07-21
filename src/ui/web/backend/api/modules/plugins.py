"""
Plugin Management Endpoints

Plugin catalog, status, and community registry.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, HTTPException

from api.modules.catalog import get_plugin_manager, PLUGIN_RUNTIME_AVAILABLE

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/plugins")
async def get_plugins_catalog() -> Dict[str, Any]:
    """
    Get list of available plugins and their status.

    Returns plugin information including:
    - Plugin ID, name, version, vendor
    - Available steps
    - Status (active, loaded, etc.)
    """
    if not PLUGIN_RUNTIME_AVAILABLE:
        return {
            "ok": True,
            "enabled": False,
            "plugins": [],
            "message": "Plugin runtime not available (flyto-core < 2.0)"
        }

    manager = get_plugin_manager()
    if not manager:
        return {
            "ok": True,
            "enabled": True,
            "plugins": [],
            "message": "No plugin directory configured"
        }

    try:
        # Discover plugins
        await manager.discover_plugins()

        plugins = []
        for plugin_id in manager.list_available_plugins():
            manifest = manager.get_manifest(plugin_id)
            if manifest:
                plugins.append({
                    "id": manifest.id,
                    "name": manifest.name,
                    "version": manifest.version,
                    "vendor": manifest.vendor,
                    "steps": [
                        {
                            "id": step.get("id"),
                            "label": step.get("label"),
                            "description": step.get("description", ""),
                        }
                        for step in manifest.steps
                    ],
                    "meta": manifest.meta,
                    "status": "available",
                })

        return {
            "ok": True,
            "enabled": True,
            "total": len(plugins),
            "plugins": plugins,
        }

    except Exception as e:
        logger.error(f"Error getting plugins: {e}")
        return {
            "ok": False,
            "enabled": True,
            "plugins": [],
            "error": str(e)
        }


@router.get("/plugins/{plugin_id:path}/status")
async def get_plugin_status(plugin_id: str) -> Dict[str, Any]:
    """
    Get detailed status of a specific plugin.

    Returns:
        Plugin status including process state and health
    """
    if not PLUGIN_RUNTIME_AVAILABLE:
        raise HTTPException(status_code=503, detail="Plugin runtime not available")

    manager = get_plugin_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")

    status = manager.get_plugin_status(plugin_id)
    if not status:
        # Try to get from manifest even if not loaded
        manifest = manager.get_manifest(plugin_id)
        if manifest:
            return {
                "ok": True,
                "plugin": {
                    "pluginId": plugin_id,
                    "version": manifest.version,
                    "status": "available",
                    "steps": [s.get("id") for s in manifest.steps],
                }
            }
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")

    return {"ok": True, "plugin": status}


# =============================================================================
# Community Plugin Registry
# =============================================================================

@router.get("/plugins/registry")
async def get_plugin_registry(
    query: Optional[str] = Query(None, description="Search query"),
    force_refresh: bool = Query(False, description="Force refresh from remote"),
) -> Dict[str, Any]:
    """
    Get available community plugins from the remote registry.

    Returns plugins that can be installed via `flyto plugin install <name>`.
    """
    try:
        from core.plugin.registry import PluginRegistry

        registry = PluginRegistry()

        if query:
            entries = registry.search(query)
        else:
            entries = registry.list_available(force_refresh=force_refresh)

        # Check which ones are installed locally
        installed_names = set()
        try:
            from core.plugin.loader import get_plugin_loader
            loader = get_plugin_loader()
            for name in loader.discover_plugins():
                installed_names.add(name)
        except Exception:
            pass

        plugins = []
        for entry in entries:
            data = entry.to_dict()
            data["installed"] = entry.name in installed_names
            plugins.append(data)

        return {
            "ok": True,
            "total": len(plugins),
            "plugins": plugins,
        }

    except ImportError:
        return {
            "ok": True,
            "total": 0,
            "plugins": [],
            "message": "Plugin registry not available (flyto-core < 2.17)",
        }
    except Exception as e:
        logger.error(f"Plugin registry error: {e}")
        return {
            "ok": False,
            "total": 0,
            "plugins": [],
            "error": str(e),
        }
