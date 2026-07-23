"""
Module Catalog Endpoints

Core catalog: tiered catalog, atomic catalog, module environment.
Shared helpers: plugin manager singleton and local template modules loader.

Internal loader/builder functions are in catalog_loaders.py.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, Depends

from config.constants import (
    get_category_defaults,
)
from services.registry_loader import (
    get_module_registry,
)
from services.module_normalizer_service import ModuleNormalizerService
from services.normalizers import normalize_atomic
from gateway.local_context import get_local_principal
from gateway.providers.base import WorkspaceContext

# Loader functions (extracted to catalog_loaders.py)
from api.modules.catalog_loaders import (
    _build_catalog_response,
    _get_tiered_catalog_impl,
    _merge_groups,
    _noop_atomic,
    _noop_plugin,
    _restore_from_cache,
)

# Plugin Runtime integration (flyto-core >= 2.0)
try:
    from core.runtime import (
        transform_manifest_to_modules,
        PluginManager,
    )
    PLUGIN_RUNTIME_AVAILABLE = True
except ImportError:
    PLUGIN_RUNTIME_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter()

# Backend startup timestamp for cache invalidation
# This changes on every backend restart, forcing frontend to refresh module cache
_BACKEND_STARTUP_TS = int(time.time())

# In-memory cache for core module catalog (composite + atomic + plugins)
# These only change on backend restart, so cache is keyed by lang
_core_catalog_cache: Dict[str, Dict[str, Any]] = {}


def _invalidate_core_cache():
    """Call when modules change (currently only on restart)."""
    _core_catalog_cache.clear()


# Local template cache: keyed by workspace_id, value is (timestamp, modules_list).
_workspace_templates_cache: Dict[str, tuple] = {}
_WORKSPACE_TEMPLATES_CACHE_TTL = 300  # 5 minutes
_WORKSPACE_TEMPLATES_CACHE_MAX = 500


def invalidate_workspace_templates_cache(workspace_id: Optional[str] = None):
    """Invalidate local template cache after CRUD operations.

    Args:
        workspace_id: Workspace to invalidate. If None, clears all.
    """
    if workspace_id:
        _workspace_templates_cache.pop(workspace_id, None)
    else:
        _workspace_templates_cache.clear()

# Plugin manager singleton
_plugin_manager: Optional["PluginManager"] = None


# =============================================================================
# Shared helpers (used by catalog.py and plugins.py)
# =============================================================================

def get_plugin_manager() -> Optional["PluginManager"]:
    """Get or create the plugin manager singleton."""
    global _plugin_manager

    if not PLUGIN_RUNTIME_AVAILABLE:
        return None

    if _plugin_manager is None:
        # Get plugin directory from environment or use default
        plugin_dir = os.environ.get(
            "FLYTO_PLUGIN_DIR",
            str(Path.home() / ".flyto" / "plugins")
        )

        if Path(plugin_dir).exists():
            _plugin_manager = PluginManager(plugin_dir=Path(plugin_dir))
            logger.info(f"Plugin manager initialized: {plugin_dir}")
        else:
            logger.debug(f"Plugin directory not found: {plugin_dir}")

    return _plugin_manager


def set_plugin_manager(manager: Optional["PluginManager"]) -> None:
    """Install the lifecycle-owned plugin manager used by catalog routes."""
    global _plugin_manager
    _plugin_manager = manager


async def get_workspace_templates_as_modules(
    workspace_id: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Load local workflow templates as reusable workflow modules.

    Templates are read from the local CE data provider.
    """
    if not workspace_id:
        return []

    # Check the local-workspace template cache.
    cache_key = workspace_id
    now = time.time()
    cached = _workspace_templates_cache.get(cache_key)
    if cached and (now - cached[0]) < _WORKSPACE_TEMPLATES_CACHE_TTL:
        return cached[1]

    try:
        from gateway.providers.hub import get_data_provider

        result = await get_data_provider().templates.list_workspace_templates(
            workspace_id=workspace_id,
            page=1,
            page_size=500,
        )
        templates = result.items or []

        # Transform to module format
        modules = []
        from services.helpers import resolve_library_id
        for item in templates:
            t = item.model_dump() if hasattr(item, "model_dump") else dict(item)
            library_id, _ = resolve_library_id(t)
            template_id = t.get("id") or t.get("template_id")
            if not template_id:
                continue
            try:
                module = ModuleNormalizerService.normalize(
                    raw=t,
                    source="template",
                    source_id=template_id,
                    library_id=library_id,
                )
                modules.append(module)
            except Exception as e:
                logger.warning(f"Failed to normalize template {template_id}: {e}")

        # Cache successful result (evict oldest if over limit)
        if len(_workspace_templates_cache) >= _WORKSPACE_TEMPLATES_CACHE_MAX:
            oldest_key = min(_workspace_templates_cache, key=lambda k: _workspace_templates_cache[k][0])
            del _workspace_templates_cache[oldest_key]
        _workspace_templates_cache[cache_key] = (now, modules)

        return modules

    except Exception as e:
        logger.warning(f"Error loading local workflow templates: {e}")
        return []


async def get_plugin_modules() -> List[Dict[str, Any]]:
    """
    Get all modules from loaded plugins.

    Returns:
        List of module items in frontend-compatible format
    """
    manager = get_plugin_manager()
    if not manager:
        return []

    try:
        # Discover plugins if not already done
        await manager.discover_plugins()

        plugin_modules = []

        # Get all discovered manifests and transform them
        for plugin_id in manager.list_available_plugins():
            manifest = manager.get_manifest(plugin_id)
            if manifest:
                # Convert PluginManifest to dict for transformer
                manifest_dict = {
                    "id": manifest.id,
                    "name": manifest.name,
                    "version": manifest.version,
                    "vendor": manifest.vendor,
                    "steps": manifest.steps,
                    "meta": manifest.meta,
                }

                # Transform manifest to module items
                modules = transform_manifest_to_modules(manifest_dict)
                plugin_modules.extend(modules)

        logger.info(f"Loaded {len(plugin_modules)} modules from plugins")
        return plugin_modules

    except Exception as e:
        logger.warning(f"Error loading plugin modules: {e}")
        return []


# =============================================================================
# Route handlers
# =============================================================================

@router.get("/environment")
async def get_module_environment() -> Dict[str, Any]:
    """
    Get current module environment settings.

    Returns the current FLYTO_ENV setting and which stability levels are visible.
    """
    try:
        from core.modules.types import (
            get_current_env,
            get_allowed_stability_levels,
            StabilityLevel
        )

        current_env = get_current_env()
        allowed = get_allowed_stability_levels(current_env)

        return {
            "ok": True,
            "environment": current_env,
            "allowed_stability_levels": [s.value for s in allowed],
            "stability_info": {
                "stable": StabilityLevel.STABLE in allowed,
                "beta": StabilityLevel.BETA in allowed,
                "alpha": StabilityLevel.ALPHA in allowed,
                "deprecated": StabilityLevel.DEPRECATED in allowed,
            }
        }
    except ImportError:
        # flyto-core < 1.12.0
        return {
            "ok": True,
            "environment": os.environ.get("FLYTO_ENV", "production"),
            "allowed_stability_levels": ["stable"],
            "stability_info": {
                "stable": True,
                "beta": False,
                "alpha": False,
                "deprecated": False,
            },
            "warning": "flyto-core < 1.12.0, stability filtering not available"
        }


@router.get("/tiered")
async def get_tiered_catalog(
    lang: str = Query(default="en", description="Language code (en, zh, ja)"),
    include_expert: bool = Query(default=True, description="Include expert/atomic modules"),
    include_plugins: bool = Query(default=True, description="Include plugin modules"),
    include_templates: bool = Query(default=True, description="Include local workflow templates"),
    skip_access_control: bool = Query(default=True, description="Skip access control (show all modules)"),
    exclude_template_id: Optional[str] = Query(default=None, description="Template ID to exclude (prevent self-reference)"),
    workspace_context: Optional[WorkspaceContext] = Depends(get_local_principal)
) -> Dict[str, Any]:
    """
    Get tiered module catalog for frontend (ADR-001)

    Returns modules organized by visibility tier:
    - default: Composite modules visible in the local builder
    - expert: Atomic modules in collapsed section
    - my-templates: Workflows saved in this local workspace

    Modules are loaded from the bundled core, local plugins, and local templates.
    Plugin modules are merged seamlessly with core modules.
    Local workflows appear as a special "my-templates" category.

    This is the primary endpoint for the new tiered UI.
    """
    try:
        return await _get_tiered_catalog_impl(
            lang=lang,
            include_expert=include_expert,
            include_plugins=include_plugins,
            include_templates=include_templates,
            skip_access_control=skip_access_control,
            exclude_template_id=exclude_template_id,
            workspace_context=workspace_context,
            plugin_runtime_available=PLUGIN_RUNTIME_AVAILABLE,
            get_plugin_modules_fn=get_plugin_modules,
            get_workspace_templates_as_modules_fn=get_workspace_templates_as_modules,
            core_catalog_cache=_core_catalog_cache,
            backend_startup_ts=_BACKEND_STARTUP_TS,
        )
    except Exception:
        logger.exception("Error in tiered catalog")
        # Return empty catalog instead of 500 error
        return {
            "ok": False,
            "error": "Unable to load module catalog",
            "version": f"error-{_BACKEND_STARTUP_TS}",
            "architecture": "ADR-001",
            "default": {"total": 0, "modules": [], "groups": []},
            "expert": {"total": 0, "modules": [], "label": "Expert Mode", "description": ""},
            "modules_by_category": {},
            "module_categories": [],
            "modules_metadata": {},
            "modulesByCategory": {},
            "moduleCategories": [],
            "modulesMetadata": {},
            "plugins": {"enabled": False, "count": 0},
            "templates": {"enabled": False, "count": 0}
        }


@router.get("/catalog")
async def get_module_catalog(
    lang: str = Query(default="en", description="Language code (en, zh, ja)"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    include_params: bool = Query(default=True, description="Include params_schema")
) -> Dict[str, Any]:
    """
    Get complete atomic module catalog for frontend (Level 2)

    Returns all registered atomic modules with metadata formatted for frontend.
    For tiered UI, use /tiered endpoint instead.
    """
    registry = get_module_registry()

    if registry is None:
        return {
            "ok": False,
            "version": "1.0.0",
            "total": 0,
            "categories": [],
            "modules": [],
            "error": "Module registry not available"
        }

    all_metadata = registry.get_all_metadata(category=category, lang=lang)

    modules = []
    categories_set = set()

    for module_id, metadata in all_metadata.items():
        # Add module_id to metadata for normalizer
        metadata_with_id = {**metadata, "module_id": module_id}
        node = normalize_atomic(metadata_with_id, level="atomic", lang=lang)

        if not include_params:
            node.pop('paramsSchema', None)
            node.pop('params_schema', None)
            node.pop('outputSchema', None)
            node.pop('output_schema', None)

        modules.append(node)
        categories_set.add(node['category'])

    modules.sort(key=lambda m: (m['category'], m['label']))

    category_counts = {}
    for m in modules:
        cat = m['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1

    categories = [
        {
            'id': cat,
            'label': cat.title(),
            'count': count,
            'icon': get_category_defaults(cat).get('icon', 'Box'),
            'color': get_category_defaults(cat).get('color', '#6C757D'),
        }
        for cat, count in sorted(category_counts.items())
    ]

    return {
        "ok": True,
        "version": "1.0.0",
        "total": len(modules),
        "categories": categories,
        "modules": modules
    }
