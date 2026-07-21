"""
Composite Module Endpoints

Get, list, and execute composite modules (pre-combined atomic modules).
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, HTTPException

from config.constants import get_category_defaults
from services.registry_loader import get_composite_registry
from services.normalizers import normalize_composite

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/composite")
async def get_composite_catalog(
    lang: str = Query(default="en", description="Language code (en, zh, ja)"),
    category: Optional[str] = Query(default=None, description="Filter by category")
) -> Dict[str, Any]:
    """
    Get composite module catalog for frontend (Level 3)

    Composite modules are pre-combined units of 3-10 atomic modules.
    These appear as primary nodes in the tiered UI.
    """
    registry = get_composite_registry()

    if registry is None:
        return {
            "ok": False,
            "version": "1.0.0",
            "total": 0,
            "categories": [],
            "modules": [],
            "groups": [],
            "error": "Composite registry not available"
        }

    try:
        all_composites = registry.list_all()
        modules = []
        groups = {}
        categories_set = set()

        for module_id, module_class in all_composites.items():
            metadata = registry.get_metadata(module_id) or {}

            if category and metadata.get('category') != category:
                continue

            # Add module_id to metadata for normalizer
            metadata_with_id = {**metadata, "module_id": module_id}
            node = normalize_composite(metadata_with_id, lang)

            if node.get('visibility') == 'hidden':
                continue

            modules.append(node)
            categories_set.add(node.get('category') or 'other')

            group = node.get('group') or 'Other'
            if group not in groups:
                groups[group] = {'count': 0, 'icon': node.get('icon', 'Package'), 'color': node.get('color', '#6C757D')}
            groups[group]['count'] += 1

        modules.sort(key=lambda m: (m.get('group') or '', m.get('label') or ''))

        categories = [
            {
                'id': cat,
                'label': cat.title(),
                'count': sum(1 for m in modules if m['category'] == cat),
                'icon': get_category_defaults(cat).get('icon', 'Box'),
                'color': get_category_defaults(cat).get('color', '#6C757D'),
            }
            for cat in sorted(categories_set)
        ]

        return {
            "ok": True,
            "version": "1.0.0",
            "total": len(modules),
            "categories": categories,
            "groups": [
                {"id": g, "label": g, "count": info['count'], "icon": info['icon'], "color": info['color']}
                for g, info in sorted(groups.items())
            ],
            "modules": modules,
            "level": 3,
            "description": "Composite modules - pre-combined atomic modules"
        }

    except Exception as e:
        logger.error(f"Error getting composite catalog: {e}")
        return {
            "ok": False,
            "version": "1.0.0",
            "total": 0,
            "categories": [],
            "modules": [],
            "error": str(e)
        }


@router.get("/composite/{composite_id:path}")
async def get_composite_module(
    composite_id: str,
    lang: str = Query(default="en", description="Language code")
) -> Dict[str, Any]:
    """Get metadata for a specific composite module"""
    registry = get_composite_registry()

    if registry is None:
        raise HTTPException(status_code=503, detail="Composite registry not available")

    metadata = registry.get_metadata(composite_id)

    if metadata is None:
        raise HTTPException(status_code=404, detail=f"Composite module not found: {composite_id}")

    # Add module_id to metadata for normalizer
    metadata_with_id = {**metadata, "module_id": composite_id}
    return {"ok": True, "module": normalize_composite(metadata_with_id, lang)}


@router.post("/composite/{composite_id:path}/execute")
async def execute_composite_module(
    composite_id: str,
    inputs: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Execute a composite module.

    Args:
        composite_id: Composite module ID (e.g., "composite.browser.search_and_notify")
        inputs: Input values for the composite module

    Returns:
        Execution result
    """
    try:
        from core.modules.composite import CompositeExecutor
        executor = CompositeExecutor()
        result = await executor.execute(composite_id, inputs or {})

        return {
            "ok": True,
            "composite_id": composite_id,
            "result": result
        }

    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Composite executor not available: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Execution failed: {str(e)}"
        )
