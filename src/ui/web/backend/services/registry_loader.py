"""
Registry Loader Service

Loads module registries from the flyto-core package bundled in the CE image or
from a wheel explicitly imported by the local operator.

Import path: core.modules
"""
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class RegistryLoader:
    """Load registries from CE's active local flyto-core installation."""

    _module_registry = None
    _composite_registry = None
    _connection_validator = None
    _initialized = False

    def _ensure_initialized(self):
        """Ensure registries are loaded on first access."""
        if self._initialized:
            return

        self._load_registries()

        # Only mark initialized if at least one registry loaded successfully
        if self._module_registry is not None or self._composite_registry is not None:
            self._initialized = True
        else:
            logger.warning("Registry loading failed — will retry on next access")

    def _load_registries(self):
        """Load all registries from flyto-core."""
        # Load ModuleRegistry (split into two steps so registry is saved even if discover fails)
        try:
            from core.modules.registry import ModuleRegistry
            self._module_registry = ModuleRegistry
        except ImportError as e:
            logger.error(f"Failed to import core.modules: {e}")
            logger.error("The bundled flyto-core runtime is unavailable")

        # Discover atomic modules (separate try so _module_registry is always saved)
        if self._module_registry is not None and self._module_registry.module_count() < 10:
            try:
                logger.info("Importing atomic modules...")
                from core.modules import atomic  # noqa: F401
                logger.info(f"Loaded {self._module_registry.module_count()} atomic modules")
            except Exception as e:
                logger.error(f"Failed to discover atomic modules: {type(e).__name__}: {e}")

        # Load CompositeRegistry
        try:
            from core.modules.composite import CompositeRegistry
            self._composite_registry = CompositeRegistry
            logger.info(f"Loaded {CompositeRegistry.module_count()} composite modules")
        except ImportError:
            logger.debug("CompositeRegistry not available")

        # Load ConnectionValidator
        try:
            from core.modules.validation import get_connection_validator
            self._connection_validator = get_connection_validator()
        except ImportError:
            logger.debug("ConnectionValidator not available")

    def get_module_registry(self) -> Optional[Any]:
        """Get atomic module registry (Level 2)"""
        self._ensure_initialized()
        return self._module_registry

    def get_composite_registry(self) -> Optional[Any]:
        """Get composite module registry (Level 3)"""
        self._ensure_initialized()
        return self._composite_registry

    def get_connection_validator(self) -> Optional[Any]:
        """Get connection validator for module connections"""
        self._ensure_initialized()
        return self._connection_validator


# Singleton instance
_loader: Optional[RegistryLoader] = None


def get_registry_loader() -> RegistryLoader:
    """Get or create registry loader singleton"""
    global _loader
    if _loader is None:
        _loader = RegistryLoader()
    return _loader


def get_module_registry() -> Optional[Any]:
    """Convenience function to get module registry"""
    return get_registry_loader().get_module_registry()


def get_composite_registry() -> Optional[Any]:
    """Convenience function to get composite registry"""
    return get_registry_loader().get_composite_registry()


def get_connection_validator() -> Optional[Any]:
    """Convenience function to get connection validator"""
    return get_registry_loader().get_connection_validator()
