"""
Base Normalizer Utilities

Shared utility functions used by all normalizers (adapters).
Split into sub-modules for maintainability.
"""

from .icons import normalize_icon, _normalize_lucide_name
from .params import (
    normalize_params_schema,
    _detect_component_type,
    _normalize_param_property,
    _translate_options,
    _convert_conditions,
    compute_default_params,
    add_hidden_markers,
    _TEXTAREA_FIELD_NAMES,
    _TEXTAREA_FIELD_SUFFIXES,
)
from .detection import (
    detect_node_type,
    detect_ai_module_flags,
    is_template_module,
    detect_requires_custom_ui,
    CUSTOM_UI_MODULE_PATTERNS,
    CUSTOM_UI_PREFIXES,
)
from .utils import get_value_with_aliases, extract_action_from_module_id

# Re-export all public symbols
__all__ = [
    # icons
    "normalize_icon",
    "_normalize_lucide_name",
    # params
    "normalize_params_schema",
    "_detect_component_type",
    "_normalize_param_property",
    "_translate_options",
    "_convert_conditions",
    "compute_default_params",
    "add_hidden_markers",
    "_TEXTAREA_FIELD_NAMES",
    "_TEXTAREA_FIELD_SUFFIXES",
    # detection
    "detect_node_type",
    "detect_ai_module_flags",
    "is_template_module",
    "detect_requires_custom_ui",
    "CUSTOM_UI_MODULE_PATTERNS",
    "CUSTOM_UI_PREFIXES",
    # utils
    "get_value_with_aliases",
    "extract_action_from_module_id",
]
