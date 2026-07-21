"""
Module Normalizer Service (ModuleCatalogService)

Unified service for normalizing module data from any source.
Single entry point for all module transformations.

Design Principles:
1. Single entry point - all sources go through this service
2. Consistent output - CanonicalModule format for all
3. Backend is single source of truth - frontend just renders
4. Error resilience - log and continue on individual failures

Usage:
    from services.module_normalizer_service import ModuleNormalizerService

    # Single module
    canonical = ModuleNormalizerService.normalize(raw_data, "atomic")

    # Batch
    canonicals = ModuleNormalizerService.normalize_batch(items, "template")

    # Get tiered catalog (aggregated from all sources)
    catalog = ModuleNormalizerService.get_tiered_catalog()
"""

import logging
from typing import List, Optional, Dict, Any, Literal, Union
from functools import lru_cache
import time

from services.template.schemas.canonical_module import CanonicalModule, SourceType
from services.normalizers.atomic import normalize_atomic
from services.normalizers.composite import normalize_composite
from services.normalizers.template import normalize_template
from services.normalizers.huggingface import normalize_huggingface

logger = logging.getLogger(__name__)


# Cache TTL in seconds (5 minutes)
CACHE_TTL = 300
_cache_timestamp = 0
_cached_catalog = None


class ModuleNormalizerService:
    """
    Unified module normalization service (ModuleCatalogService).

    All data sources must go through this service before being sent to frontend.
    Ensures consistent output format regardless of source.
    """

    @staticmethod
    def normalize(
        raw: Dict[str, Any],
        source: SourceType,
        source_id: Optional[str] = None,
        lang: str = "en",
        level: str = "atomic",
        library_id: Optional[str] = None,
    ) -> CanonicalModule:
        """
        Normalize a single module from any source.

        Args:
            raw: Raw module data from source
            source: Source type (atomic, composite, plugin, template, huggingface)
            source_id: Optional source identifier (e.g., template_id, plugin_id)
            lang: Language code for i18n (default "en")
            level: Module level for atomic modules (default "atomic")
            library_id: Library entry ID for templates (purchase_id/fork_id)

        Returns:
            CanonicalModule with all fields populated

        Raises:
            ValueError: If source type is unknown
        """
        if source == "atomic":
            return normalize_atomic(raw, level=level)
        elif source == "composite":
            return normalize_composite(raw, lang=lang)
        elif source == "plugin":
            # Plugin modules currently use composite normalizer
            # They have similar structure but different source tracking
            result = normalize_composite(raw, lang=lang)
            result['source'] = 'plugin'
            # Update sourceData with plugin info
            source_data = result.get('sourceData', {})
            source_data['pluginId'] = source_id or raw.get('plugin_id')
            result['sourceData'] = source_data
            return result
        elif source == "template":
            template_id = source_id or raw.get('id') or raw.get('template_id')
            if not template_id:
                raise ValueError("Template source requires source_id or 'id' in raw data")
            return normalize_template(raw, template_id, library_id=library_id)
        elif source == "huggingface":
            return normalize_huggingface(raw)
        else:
            raise ValueError(f"Unknown source type: {source}")

    @staticmethod
    def normalize_batch(
        items: List[Dict[str, Any]],
        source: SourceType,
        lang: str = "en",
        level: str = "atomic"
    ) -> List[CanonicalModule]:
        """
        Normalize a batch of modules from the same source.

        Logs errors but continues processing on individual failures.

        Args:
            items: List of raw module data
            source: Source type for all items
            lang: Language code for i18n
            level: Module level for atomic modules

        Returns:
            List of CanonicalModule (may be shorter than input if errors occur)
        """
        results = []

        for item in items:
            try:
                # Extract source_id based on source type
                source_id = None
                if source == "template":
                    source_id = item.get('id') or item.get('template_id')
                elif source == "plugin":
                    source_id = item.get('plugin_id')

                normalized = ModuleNormalizerService.normalize(
                    raw=item,
                    source=source,
                    source_id=source_id,
                    lang=lang,
                    level=level
                )
                results.append(normalized)
            except Exception as e:
                # Log but continue - don't let one bad module break the whole catalog
                item_id = (
                    item.get('module_id') or
                    item.get('moduleId') or
                    item.get('id') or
                    'unknown'
                )
                logger.warning(f"Failed to normalize {source} module '{item_id}': {e}")

        return results

    @staticmethod
    def normalize_mixed(
        items: List[Dict[str, Any]],
        lang: str = "en"
    ) -> List[CanonicalModule]:
        """
        Normalize a batch of modules from mixed sources.

        Each item must have a 'source' field indicating its type.

        Args:
            items: List of raw module data with 'source' field
            lang: Language code for i18n

        Returns:
            List of CanonicalModule
        """
        results = []

        for item in items:
            try:
                source = item.get('source', 'atomic')
                if source not in ('atomic', 'composite', 'plugin', 'template', 'huggingface'):
                    logger.warning(f"Unknown source type '{source}', defaulting to atomic")
                    source = 'atomic'

                normalized = ModuleNormalizerService.normalize(
                    raw=item,
                    source=source,
                    lang=lang
                )
                results.append(normalized)
            except Exception as e:
                item_id = item.get('module_id') or item.get('id') or 'unknown'
                logger.warning(f"Failed to normalize mixed module '{item_id}': {e}")

        return results

    @staticmethod
    def build_category_tree(modules: List[CanonicalModule]) -> Dict[str, Any]:
        """
        Build category tree from normalized modules.

        Args:
            modules: List of normalized modules

        Returns:
            Dict with categories, each containing modules and metadata
        """
        categories = {}

        for module in modules:
            category = module.get('category', 'other')

            if category not in categories:
                categories[category] = {
                    'id': category,
                    'label': category.title(),
                    'icon': module.get('icon', {"type": "lucide", "value": "Package"}),
                    'color': module.get('color', '#6C757D'),
                    'modules': [],
                    'count': 0
                }

            categories[category]['modules'].append(module)
            categories[category]['count'] += 1

        return categories

    @staticmethod
    def build_modules_by_id(modules: List[CanonicalModule]) -> Dict[str, CanonicalModule]:
        """
        Build module lookup dict by module ID.

        Args:
            modules: List of normalized modules

        Returns:
            Dict mapping moduleId -> CanonicalModule
        """
        result = {}

        for module in modules:
            module_id = module.get('moduleId')
            if module_id:
                result[module_id] = module

        return result

    @staticmethod
    def build_groups(modules: List[CanonicalModule]) -> List[Dict[str, Any]]:
        """
        Build group list from normalized modules.

        Args:
            modules: List of normalized modules

        Returns:
            List of group dicts with id, label, count, icon, color
        """
        groups = {}

        for module in modules:
            group = module.get('group', 'Other')

            if group not in groups:
                groups[group] = {
                    'id': group,
                    'label': group,
                    'icon': module.get('icon', {"type": "lucide", "value": "Package"}),
                    'color': module.get('color', '#6C757D'),
                    'count': 0
                }

            groups[group]['count'] += 1

        return sorted(groups.values(), key=lambda g: g['label'])

    @staticmethod
    def build_tiered_view(modules: List[CanonicalModule]) -> Dict[str, List[CanonicalModule]]:
        """
        Build tiered view of modules.

        Args:
            modules: List of normalized modules

        Returns:
            Dict with tiers: featured, standard, toolkit, internal
        """
        tiers = {
            'featured': [],
            'standard': [],
            'toolkit': [],
            'internal': []
        }

        for module in modules:
            tier = module.get('tier', 'standard')
            if tier not in tiers:
                tier = 'standard'
            tiers[tier].append(module)

        return tiers

    @staticmethod
    def get_tiered_catalog(
        lang: str = "en",
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get aggregated tiered catalog from all sources.

        Uses 5-minute cache for performance.

        Args:
            lang: Language code for i18n
            force_refresh: Force cache refresh

        Returns:
            Tiered catalog dict with modules, categories, groups
        """
        global _cache_timestamp, _cached_catalog

        current_time = time.time()

        # Check cache
        if not force_refresh and _cached_catalog and (current_time - _cache_timestamp) < CACHE_TTL:
            return _cached_catalog

        # Load modules from all sources
        all_modules = []

        try:
            # Load atomic modules
            from services.registry_loader import get_module_registry
            atomic_registry = get_module_registry()
            if atomic_registry:
                atomic_metadata = atomic_registry.get_all_metadata()
                atomic_modules = ModuleNormalizerService.normalize_batch(
                    list(atomic_metadata.values()),
                    source="atomic",
                    lang=lang
                )
                all_modules.extend(atomic_modules)
                logger.info(f"Loaded {len(atomic_modules)} atomic modules")
        except Exception as e:
            logger.warning(f"Failed to load atomic modules: {e}")

        try:
            # Load composite modules
            from services.registry_loader import get_composite_registry
            composite_registry = get_composite_registry()
            if composite_registry:
                composite_metadata = composite_registry.get_all_metadata()
                composite_modules = ModuleNormalizerService.normalize_batch(
                    list(composite_metadata.values()),
                    source="composite",
                    lang=lang
                )
                all_modules.extend(composite_modules)
                logger.info(f"Loaded {len(composite_modules)} composite modules")
        except Exception as e:
            logger.warning(f"Failed to load composite modules: {e}")

        # Build catalog
        catalog = {
            'modules': all_modules,
            'byId': ModuleNormalizerService.build_modules_by_id(all_modules),
            'categories': ModuleNormalizerService.build_category_tree(all_modules),
            'groups': ModuleNormalizerService.build_groups(all_modules),
            'tiers': ModuleNormalizerService.build_tiered_view(all_modules),
            'count': len(all_modules),
            'timestamp': current_time,
        }

        # Update cache
        _cached_catalog = catalog
        _cache_timestamp = current_time

        return catalog

    @staticmethod
    def invalidate_cache():
        """Invalidate the module catalog cache."""
        global _cache_timestamp, _cached_catalog
        _cache_timestamp = 0
        _cached_catalog = None


# Singleton instance for convenience
_normalizer_service: Optional[ModuleNormalizerService] = None


def get_normalizer_service() -> ModuleNormalizerService:
    """Get the singleton normalizer service instance."""
    global _normalizer_service
    if _normalizer_service is None:
        _normalizer_service = ModuleNormalizerService()
    return _normalizer_service


# Alias for new naming
ModuleCatalogService = ModuleNormalizerService
get_catalog_service = get_normalizer_service
