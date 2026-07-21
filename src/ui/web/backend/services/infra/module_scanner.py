"""
Module Scanner - Get modules from pip-installed flyto-core

This module provides a compatibility wrapper for code that previously
scanned local files. Now it simply loads from pip-installed package.

All modules are imported from: core.modules (pip package)
"""
import logging
from typing import Dict, Any, Optional

from config.constants import CATEGORY_DEFAULTS
from services.registry_loader import get_module_registry, get_composite_registry

logger = logging.getLogger(__name__)


class ModuleScanner:
    """
    Load modules from pip-installed flyto-core.

    This is a compatibility wrapper - all modules are now loaded
    from the pip-installed package, not scanned from local files.
    """

    def __init__(self, core_path: Optional[str] = None):
        """
        Initialize scanner.

        Args:
            core_path: Ignored (kept for backward compatibility)
        """
        if core_path:
            logger.warning(
                "core_path argument is deprecated. "
                "Modules are loaded from pip package."
            )

    def scan_modules(self) -> Dict[str, Any]:
        """
        Get all registered modules from pip-installed flyto-core.

        Returns:
            {
                "modules": [...],
                "count": int,
                "categories": {...},
                "status": "success" | "error",
                "message": str
            }
        """
        try:
            registry = get_module_registry()

            if registry is None:
                return {
                    "modules": [],
                    "count": 0,
                    "categories": {},
                    "status": "error",
                    "message": "flyto-core not installed. Run: pip install flyto-core"
                }

            all_metadata = registry.get_all_metadata()

            # Group by category
            categories = {}
            for module_id, metadata in all_metadata.items():
                cat = metadata.get('category', 'other')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(metadata)

            logger.info(f"Loaded {len(all_metadata)} modules from flyto-core")

            return {
                "modules": list(all_metadata.values()),
                "count": len(all_metadata),
                "categories": categories,
                "status": "success",
                "message": f"Loaded {len(all_metadata)} modules from pip package"
            }

        except ImportError as e:
            logger.error(f"Failed to import core.modules: {e}")
            return {
                "modules": [],
                "count": 0,
                "categories": {},
                "status": "error",
                "message": "flyto-core not installed. Run: pip install flyto-core"
            }
        except Exception as e:
            logger.error(f"Error loading modules: {e}")
            return {
                "modules": [],
                "count": 0,
                "categories": {},
                "status": "error",
                "message": str(e)
            }

    def get_category_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about available categories.

        Returns:
            {
                "browser": {
                    "label": "Browser",
                    "icon": "Monitor",
                    "description": "...",
                    "count": 5
                },
                ...
            }
        """
        try:
            registry = get_module_registry()

            if registry is None:
                return {}

            all_metadata = registry.get_all_metadata()

            categories = {}
            for module_id, metadata in all_metadata.items():
                cat = metadata.get('category', 'other')

                if cat not in categories:
                    categories[cat] = {
                        "name": cat,
                        "label": cat.capitalize(),
                        "icon": self._get_category_icon(cat),
                        "description": f"{cat.capitalize()} automation modules",
                        "count": 0
                    }

                categories[cat]["count"] += 1

            return categories

        except Exception as e:
            logger.error(f"Error getting category metadata: {e}")
            return {}

    @staticmethod
    def _get_category_icon(category: str) -> str:
        """Map category to Lucide icon name"""
        defaults = CATEGORY_DEFAULTS.get(category.lower(), {})
        return defaults.get('icon', 'Box')
