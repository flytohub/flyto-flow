"""
Module Version Endpoints

Version info and hot reload endpoints.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Query, HTTPException

from config.constants import get_category_defaults
from services.registry_loader import get_module_registry
from services.normalizers import normalize_atomic

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/version")
async def get_module_version() -> Dict[str, Any]:
    """
    Get current module version for cache validation.
    Frontend can poll this endpoint to detect updates.
    """
    try:
        from services.infra.module_reloader import get_module_reloader
        reloader = get_module_reloader()
        return reloader.version_info
    except ImportError:
        return {
            "version": "1.0.0",
            "updated_at": None,
            "module_count": 0,
            "composite_count": 0
        }


@router.post("/reload")
async def reload_modules(
    force: bool = Query(default=False, description="Force reload even within rate limit"),
    upgrade: bool = Query(default=False, description="Also upgrade via pip from PyPI")
) -> Dict[str, Any]:
    """
    Hot reload modules from pip-installed flyto-core.

    Use this after:
    - /api/core/update (pip upgrade from PyPI)
    - /api/core/upload (.whl upload)

    Query params:
    - force: Skip rate limiting
    - upgrade: Also run pip upgrade before reload
    """
    try:
        from services.infra.module_reloader import get_module_reloader
        from websocket.module_sync import get_module_sync_manager

        reloader = get_module_reloader()
        manager = get_module_sync_manager()

        async def on_reload_complete(version_info):
            await manager.broadcast_module_update(version_info)

        reloader.add_listener(on_reload_complete)

        if upgrade:
            result = await reloader.upgrade_and_reload()
        else:
            result = await reloader.reload(force=force)

        reloader.remove_listener(on_reload_complete)

        if result["success"]:
            return {
                "status": "success",
                "version": result.get("version"),
                "modules": result.get("modules"),
                "timestamp": result.get("timestamp"),
                "pip": result.get("pip")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Reload failed"))

    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Module reloader not available: {str(e)}"
        )


@router.get("/categories")
async def get_categories() -> List[Dict[str, Any]]:
    """Get all available module categories"""
    registry = get_module_registry()

    if registry is None:
        return []

    all_metadata = registry.get_all_metadata()

    category_counts = {}
    for module_id, metadata in all_metadata.items():
        cat = metadata.get('category', module_id.split('.')[0])
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return [
        {
            'id': cat,
            'label': cat.title(),
            'count': count,
            'icon': get_category_defaults(cat).get('icon', 'Box'),
            'color': get_category_defaults(cat).get('color', '#6C757D'),
            'nodeType': get_category_defaults(cat).get('nodeType', 'utility'),
        }
        for cat, count in sorted(category_counts.items())
    ]


@router.get("/{module_id:path}")
async def get_module(
    module_id: str,
    lang: str = Query(default="en", description="Language code")
) -> Dict[str, Any]:
    """Get metadata for a specific module"""
    registry = get_module_registry()

    if registry is None:
        raise HTTPException(status_code=503, detail="Module registry not available")

    metadata = registry.get_metadata(module_id, lang=lang)

    if metadata is None:
        raise HTTPException(status_code=404, detail=f"Module not found: {module_id}")

    # Add module_id to metadata for normalizer
    metadata_with_id = {**metadata, "module_id": module_id}
    return normalize_atomic(metadata_with_id, level="atomic")
