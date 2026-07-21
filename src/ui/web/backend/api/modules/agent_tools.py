"""
Agent Tools Endpoints

Get and resolve module tools available for AI Agent use.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from config.constants import get_category_defaults
from services.registry_loader import get_module_registry

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/tools")
async def get_agent_tools(
    lang: str = Query(default="en", description="Language code"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
) -> Dict[str, Any]:
    """
    Get modules available as tools for AI Agent.

    Returns modules that can be used as tools in llm.agent.
    Filtered to only include modules suitable for agent use.
    """
    registry = get_module_registry()

    if registry is None:
        return {
            "ok": False,
            "tools": [],
            "categories": [],
            "error": "Module registry not available"
        }

    all_metadata = registry.get_all_metadata(category=category, lang=lang)

    tools = []
    categories_map = {}

    # Exclude flow control and internal modules
    excluded_categories = {'flow', 'internal', 'system', 'composite'}
    excluded_modules = {'llm.agent'}  # Don't allow agent to use itself

    for module_id, metadata in all_metadata.items():
        cat = metadata.get('category') or 'other'

        # Skip excluded
        if cat in excluded_categories:
            continue
        if module_id in excluded_modules:
            continue

        # Build tool entry
        tool = {
            'id': module_id,
            'label': metadata.get('label', module_id),
            'description': metadata.get('description', ''),
            'category': cat,
            'icon': metadata.get('icon', 'Box'),
            'color': metadata.get('color', '#6C757D'),
            'params_schema': metadata.get('params_schema', [])
        }
        tools.append(tool)

        # Track categories
        if cat not in categories_map:
            cat_defaults = get_category_defaults(cat)
            categories_map[cat] = {
                'id': cat,
                'pattern': f'{cat}.*',
                'label': cat.title(),
                'icon': cat_defaults.get('icon', 'Box'),
                'color': cat_defaults.get('color', '#6C757D'),
                'count': 0
            }
        categories_map[cat]['count'] += 1

    tools.sort(key=lambda t: (t['category'], t['label']))
    categories = sorted(categories_map.values(), key=lambda c: c['label'])

    return {
        "ok": True,
        "total": len(tools),
        "tools": tools,
        "categories": categories
    }


@router.get("/tools/resolve")
async def resolve_tool_patterns(
    patterns: str = Query(..., description="Comma-separated tool patterns like 'browser.*,http.*'"),
) -> Dict[str, Any]:
    """
    Resolve tool patterns to actual module IDs.

    Given patterns like 'browser.*,file.*', returns the matching module IDs.
    Used by AI Agent to convert category wildcards to specific modules.
    """
    registry = get_module_registry()

    if registry is None:
        return {"ok": False, "tools": [], "error": "Module registry not available"}

    all_metadata = registry.get_all_metadata()
    pattern_list = [p.strip() for p in patterns.split(',') if p.strip()]

    resolved = []

    for module_id in all_metadata.keys():
        for pattern in pattern_list:
            if pattern.endswith('.*'):
                # Category wildcard
                prefix = pattern[:-2]
                if module_id.startswith(prefix + '.'):
                    resolved.append(module_id)
                    break
            elif module_id == pattern:
                # Exact match
                resolved.append(module_id)
                break

    return {
        "ok": True,
        "patterns": pattern_list,
        "resolved": sorted(set(resolved)),
        "count": len(set(resolved))
    }
