"""
Backend Configuration Module
Centralized configuration for all backend settings
"""

from config.settings import Settings, get_settings
from config.paths import PathResolver, get_path_resolver
from config.constants import (
    CATEGORY_DEFAULTS,
    DEFAULT_VISIBILITY_CATEGORIES,
    APP_NAME,
    APP_VERSION
)

__all__ = [
    'Settings',
    'get_settings',
    'PathResolver',
    'get_path_resolver',
    'CATEGORY_DEFAULTS',
    'DEFAULT_VISIBILITY_CATEGORIES',
    'APP_NAME',
    'APP_VERSION',
]
