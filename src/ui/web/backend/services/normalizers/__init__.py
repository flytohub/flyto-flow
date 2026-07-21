"""
Module Adapters (Normalizers)

Each adapter converts a specific source type to CanonicalModule format.
"""

from .atomic import normalize_atomic
from .composite import normalize_composite
from .template import normalize_template
from .huggingface import normalize_huggingface
from .base import (
    normalize_icon,
    normalize_params_schema,
    compute_default_params,
    add_hidden_markers,
    detect_node_type,
    detect_ai_module_flags,
    is_template_module,
    get_value_with_aliases,
    extract_action_from_module_id,
)

__all__ = [
    "normalize_atomic",
    "normalize_composite",
    "normalize_template",
    "normalize_huggingface",
    "normalize_icon",
    "normalize_params_schema",
    "compute_default_params",
    "add_hidden_markers",
    "detect_node_type",
    "detect_ai_module_flags",
    "is_template_module",
    "get_value_with_aliases",
    "extract_action_from_module_id",
]
