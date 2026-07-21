"""
Catalog Loader Functions

Internal loader/builder functions for the tiered module catalog.
Extracted from catalog.py for maintainability.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from services.registry_loader import (
    get_module_registry,
    get_composite_registry,
)
from services.normalizers import normalize_atomic, normalize_composite
from services.infra.module_access import get_module_access_service
from gateway.providers.base import UserInfo

logger = logging.getLogger(__name__)


async def _load_composite_modules(
    composite_registry,
    access_service,
    skip_access_control: bool,
    current_user: Optional[UserInfo],
    lang: str,
) -> tuple:
    """Load composite modules and their group metadata.

    Returns:
        (modules list, groups dict)
    """
    modules = []
    groups = {}

    if not composite_registry:
        return modules, groups

    try:
        all_composites = composite_registry.list_all()
        for module_id, module_class in all_composites.items():
            # Access control: Check if user can access this module (unless skipped)
            if not skip_access_control:
                has_access = await access_service.check_module_access(current_user, module_id)
                if not has_access:
                    continue

            metadata = composite_registry.get_metadata(module_id) or {}
            # Add module_id to metadata for normalizer
            metadata_with_id = {**metadata, "module_id": module_id}
            node = normalize_composite(metadata_with_id, lang)

            visibility = node.get('visibility', 'default')
            if visibility != 'hidden':
                modules.append(node)

                # NOTE: Use `or` instead of get(key, default) because get() returns None
                # when the key exists but value is None, causing sort() to fail with:
                # "'<' not supported between instances of 'str' and 'NoneType'"
                group = node.get('group') or 'Other'
                if group not in groups:
                    groups[group] = {'count': 0, 'icon': node.get('icon', 'Package'), 'color': node.get('color', '#6C757D')}
                groups[group]['count'] += 1
    except Exception as e:
        logger.warning(f"Error loading composite modules: {e}")

    return modules, groups


async def _load_atomic_modules(
    atomic_registry,
    access_service,
    skip_access_control: bool,
    current_user: Optional[UserInfo],
    lang: str,
) -> tuple:
    """Load atomic modules split into default and expert tiers.

    Returns:
        (default_modules, expert_modules)
    """
    default_modules = []
    expert_modules = []

    if not atomic_registry:
        return default_modules, expert_modules

    try:
        all_metadata = atomic_registry.get_all_metadata(lang=lang)
        for module_id, metadata in all_metadata.items():
            # Skip base template.invoke -- users see their templates as template.invoke:{id}
            if module_id == 'template.invoke':
                continue

            # Access control: Check if user can access this module (unless skipped)
            if not skip_access_control:
                has_access = await access_service.check_module_access(current_user, module_id)
                if not has_access:
                    continue

            # Use new normalizer - it sets tier and visibility correctly
            # normalize_atomic expects raw_metadata with module_id field
            metadata_with_id = {**metadata, "module_id": module_id}
            node = normalize_atomic(metadata_with_id, level="atomic", lang=lang)

            # Use tier from normalized result
            # Tiers: featured, standard, toolkit, internal
            tier = node.get('tier', 'standard')

            # Map tier to list placement
            # internal -> hidden (skip)
            # toolkit -> expert (collapsed section)
            # standard/featured -> default (visible)
            if tier == 'internal':
                continue
            elif tier == 'toolkit':
                expert_modules.append(node)
            else:
                # standard or featured
                default_modules.append(node)
    except Exception as e:
        logger.warning(f"Error loading atomic modules: {e}")

    return default_modules, expert_modules


async def _load_plugin_modules(
    access_service,
    skip_access_control: bool,
    current_user: Optional[UserInfo],
    *,
    plugin_runtime_available: bool,
    get_plugin_modules_fn,
) -> tuple:
    """Load plugin modules and split into default/expert tiers.

    Args:
        plugin_runtime_available: Whether plugin runtime is available.
        get_plugin_modules_fn: Callable to get plugin modules list.

    Returns:
        (default_plugins, expert_plugins, groups_update)
    """
    default_plugins = []
    expert_plugins = []
    groups_update = {}

    if not plugin_runtime_available:
        return default_plugins, expert_plugins, groups_update

    try:
        plugin_modules_list = await get_plugin_modules_fn()

        for module in plugin_modules_list:
            # Determine visibility based on plugin UI settings
            visibility = module.get("ui", {}).get("visibility", "default")
            if visibility == "hidden":
                continue

            # Plugin modules go to default tier (visible alongside composites)
            # unless marked as toolkit/expert
            tier = module.get("tier", "standard")
            if tier == "toolkit":
                expert_plugins.append(module)
            else:
                default_plugins.append(module)

                # Track groups for plugins
                group = module.get("ui", {}).get("group") or module.get("category", "Other")
                if group not in groups_update:
                    groups_update[group] = {
                        'count': 0,
                        'icon': module.get('icon', 'Package'),
                        'color': module.get('color', '#6C757D')
                    }
                groups_update[group]['count'] += 1

        logger.debug(f"Added {len(plugin_modules_list)} plugin modules to catalog")

    except Exception as e:
        logger.warning(f"Error loading plugin modules: {e}")

    return default_plugins, expert_plugins, groups_update


async def _load_user_template_modules(
    current_user: Optional[UserInfo],
    exclude_template_id: Optional[str],
    auth_header: Optional[str] = None,
    *,
    get_user_templates_as_modules_fn,
) -> tuple:
    """Load user templates transformed as modules.

    Args:
        get_user_templates_as_modules_fn: Callable to get user templates as modules.

    Returns:
        (modules, groups_update)
    """
    modules = []
    groups_update = {}

    try:
        user_id = None
        if current_user:
            user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        user_template_modules = await get_user_templates_as_modules_fn(user_id, auth_header=auth_header)

        for module in user_template_modules:
            # Skip current template to prevent self-reference (infinite loop)
            # templateId and libraryId are nested in sourceData (from normalize_template)
            if exclude_template_id:
                source_data = module.get('sourceData') or {}
                template_id = source_data.get('templateId')
                library_id = source_data.get('libraryId')
                if template_id == exclude_template_id or library_id == exclude_template_id:
                    continue

            # User templates always go to default tier (visible)
            modules.append(module)

            # Track groups for templates
            group = module.get("group", "My Templates")
            if group not in groups_update:
                groups_update[group] = {
                    'count': 0,
                    'icon': module.get('icon', 'FileText'),
                    'color': module.get('color', '#8B5CF6')
                }
            groups_update[group]['count'] += 1

        excluded = len(user_template_modules) - len(modules)
        logger.debug(f"Added {len(modules)} user templates to catalog (excluded: {excluded})")

    except Exception as e:
        logger.warning(f"Error loading user templates: {e}")

    return modules, groups_update


async def _build_catalog_response(
    default_modules: List[Dict[str, Any]],
    expert_modules: List[Dict[str, Any]],
    groups: Dict[str, Any],
    plugin_count: int,
    template_count: int,
    include_templates: bool,
    current_user: Optional[UserInfo],
    *,
    plugin_runtime_available: bool = False,
    backend_startup_ts: int = 0,
) -> Dict[str, Any]:
    """Assemble the final tiered catalog response dict.

    Sorts modules, pre-computes category structures, and builds the response.
    """
    default_modules.sort(key=lambda m: (m.get('group') or '', m.get('label') or ''))
    expert_modules.sort(key=lambda m: (m.get('category') or '', m.get('label') or ''))

    # S-Grade: Pre-compute structures for frontend (no frontend computation needed)
    modules_by_category = {}
    module_categories = []
    modules_metadata = {}
    all_modules = default_modules + expert_modules

    for mod in all_modules:
        cat = mod.get('category') or 'other'
        module_id = mod.get('moduleId') or mod.get('module_id')

        # Build modulesByCategory (what frontend calls availableSteps)
        if cat not in modules_by_category:
            modules_by_category[cat] = []
        modules_by_category[cat].append(mod)

        # Build modulesMetadata
        if module_id:
            modules_metadata[module_id] = mod

    # Build moduleCategories list
    for cat in sorted(modules_by_category.keys()):
        cat_modules = modules_by_category[cat]
        if cat_modules:
            first_mod = cat_modules[0]
            module_categories.append({
                'name': cat,
                'label': cat.title(),
                'icon': first_mod.get('icon', 'Package'),
                'color': first_mod.get('color', '#6C757D')
            })

    # Get flyto-core version for cache invalidation
    # Include backend startup timestamp to force cache refresh on restart
    try:
        from importlib.metadata import version as pkg_version
        core_version = pkg_version("flyto-core")
    except Exception:
        core_version = "unknown"
    cache_version = f"{core_version}-{backend_startup_ts}"

    return {
        "ok": True,
        "version": cache_version,
        "architecture": "ADR-001",
        "default": {
            "total": len(default_modules),
            "modules": default_modules,
            "groups": [
                {"id": g, "label": g, "count": info['count'], "icon": info['icon'], "color": info['color']}
                for g, info in sorted(groups.items())
            ]
        },
        "expert": {
            "total": len(expert_modules),
            "modules": expert_modules,
            "label": "Expert Mode",
            "description": "Advanced atomic modules for power users"
        },
        # S-Grade: Pre-computed structures for direct frontend assignment
        # Keep snake_case for existing API clients and camelCase for raw
        # frontend consumers that do not pass through the axios case converter.
        "modules_by_category": modules_by_category,
        "module_categories": module_categories,
        "modules_metadata": modules_metadata,
        "modulesByCategory": modules_by_category,
        "moduleCategories": module_categories,
        "modulesMetadata": modules_metadata,
        # Plugin Runtime status
        "plugins": {
            "enabled": plugin_runtime_available,
            "count": plugin_count,
        },
        # User templates (my-templates)
        "templates": {
            "enabled": include_templates,
            "count": template_count,
        }
    }


async def _noop_atomic():
    """Fallback for when atomic modules are not requested."""
    return [], []


async def _noop_plugin():
    """Fallback for when plugin modules are not requested."""
    return [], [], {}


def _restore_from_cache(cached: dict) -> tuple:
    """Deep-copy cached core catalog so user-specific modules can be appended safely."""
    return (
        list(cached['default_modules']),
        list(cached['expert_modules']),
        {g: dict(info) for g, info in cached['groups'].items()},
    )


async def _load_core_modules(
    lang: str,
    include_expert: bool,
    include_plugins: bool,
    skip_access_control: bool,
    current_user: Optional[UserInfo],
    *,
    plugin_runtime_available: bool,
    get_plugin_modules_fn,
    core_catalog_cache: Dict[str, Dict[str, Any]],
) -> tuple:
    """Load composite, atomic, and plugin modules in parallel and cache the result.

    Args:
        plugin_runtime_available: Whether plugin runtime is available.
        get_plugin_modules_fn: Callable to get plugin modules list.
        core_catalog_cache: Mutable cache dict to store results in.
    """
    composite_registry = get_composite_registry()
    atomic_registry = get_module_registry()

    access_service = get_module_access_service()
    if not skip_access_control:
        await access_service.get_accessible_modules(current_user)

    results = await asyncio.gather(
        _load_composite_modules(composite_registry, access_service, skip_access_control, current_user, lang),
        _load_atomic_modules(atomic_registry, access_service, skip_access_control, current_user, lang) if include_expert else _noop_atomic(),
        _load_plugin_modules(
            access_service, skip_access_control, current_user,
            plugin_runtime_available=plugin_runtime_available,
            get_plugin_modules_fn=get_plugin_modules_fn,
        ) if include_plugins else _noop_plugin(),
    )

    default_modules, groups = results[0]
    atomic_default, atomic_expert = results[1]
    plugin_default, plugin_expert, plugin_groups = results[2]

    expert_modules = []
    default_modules.extend(atomic_default)
    expert_modules.extend(atomic_expert)
    default_modules.extend(plugin_default)
    expert_modules.extend(plugin_expert)
    _merge_groups(groups, plugin_groups)

    # Cache for subsequent requests
    core_catalog_cache[lang] = {
        'default_modules': list(default_modules),
        'expert_modules': list(expert_modules),
        'groups': {g: dict(info) for g, info in groups.items()},
    }

    return default_modules, expert_modules, groups


def _merge_groups(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """Merge source group counts into target, creating entries as needed."""
    for g, info in source.items():
        if g not in target:
            target[g] = info
        else:
            target[g]['count'] += info['count']


async def _get_tiered_catalog_impl(
    lang: str,
    include_expert: bool,
    include_plugins: bool,
    include_templates: bool,
    skip_access_control: bool,
    exclude_template_id: Optional[str],
    current_user: Optional[UserInfo],
    auth_header: Optional[str] = None,
    *,
    plugin_runtime_available: bool,
    get_plugin_modules_fn,
    get_user_templates_as_modules_fn,
    core_catalog_cache: Dict[str, Dict[str, Any]],
    backend_startup_ts: int,
) -> Dict[str, Any]:
    """Internal implementation of tiered catalog.

    Args:
        plugin_runtime_available: Whether plugin runtime is available.
        get_plugin_modules_fn: Callable to get plugin modules list.
        get_user_templates_as_modules_fn: Callable to get user templates as modules.
        core_catalog_cache: Mutable cache dict (shared with catalog.py).
        backend_startup_ts: Backend startup timestamp for cache versioning.
    """
    core_cached = core_catalog_cache.get(lang)

    if core_cached:
        default_modules, expert_modules, groups = _restore_from_cache(core_cached)
    else:
        default_modules, expert_modules, groups = await _load_core_modules(
            lang, include_expert, include_plugins, skip_access_control, current_user,
            plugin_runtime_available=plugin_runtime_available,
            get_plugin_modules_fn=get_plugin_modules_fn,
            core_catalog_cache=core_catalog_cache,
        )

    # Append user templates (user-specific, uses its own cache)
    template_count = 0
    if include_templates:
        template_modules, template_groups = await _load_user_template_modules(
            current_user, exclude_template_id, auth_header=auth_header,
            get_user_templates_as_modules_fn=get_user_templates_as_modules_fn,
        )
        default_modules.extend(template_modules)
        template_count = len(template_modules)
        _merge_groups(groups, template_groups)

    plugin_count = sum(1 for m in default_modules + expert_modules if m.get("source") == "plugin")

    return await _build_catalog_response(
        default_modules=default_modules,
        expert_modules=expert_modules,
        groups=groups,
        plugin_count=plugin_count,
        template_count=template_count,
        include_templates=include_templates,
        current_user=current_user,
        plugin_runtime_available=plugin_runtime_available,
        backend_startup_ts=backend_startup_ts,
    )
