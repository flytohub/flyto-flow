"""
Composite Module Adapter

Converts composite module metadata to CanonicalModule format.
Composite modules are pre-combined units of atomic modules.
"""

from typing import Dict, Any

from config.constants import CATEGORY_DEFAULTS, DEFAULT_CATEGORY_META
from services.template.schemas.canonical_module import (
    CanonicalModule,
    create_canonical_module,
    add_snake_case_aliases,
    convert_snake_to_camel,
    INCLUDE_SNAKE_CASE_ALIASES,
)
from services.node_config import enrich_module_with_node_config
from .base import (
    normalize_icon,
    normalize_params_schema,
    compute_default_params,
    add_hidden_markers,
    detect_node_type,
    detect_ai_module_flags,
    detect_requires_custom_ui,
    is_template_module,
    get_value_with_aliases,
)


def get_category_meta(category: str) -> dict:
    """Get category metadata with fallback."""
    return CATEGORY_DEFAULTS.get(category.lower(), DEFAULT_CATEGORY_META)


def normalize_composite(raw: Dict[str, Any], lang: str = "en") -> CanonicalModule:
    """
    Convert composite module metadata to CanonicalModule format.

    Input comes from: registry_loader.py -> get_composite_registry().get_metadata()

    Args:
        raw: Raw metadata from composite registry
        lang: Language code for i18n (default "en")

    Returns:
        CanonicalModule with all fields populated
    """
    module_id = get_value_with_aliases(raw, "module_id", "moduleId", default="unknown")
    category = raw.get("category", "composite")
    defaults = get_category_meta(category)

    # Handle multi-language labels (flyto-core internal format)
    label_raw = get_value_with_aliases(raw, "ui_label", "label", default=module_id)
    if isinstance(label_raw, dict):
        label_raw = label_raw.get(lang) or label_raw.get("en") or module_id

    description_raw = get_value_with_aliases(raw, "ui_description", "description", default="")
    if isinstance(description_raw, dict):
        description_raw = description_raw.get(lang) or description_raw.get("en") or ""

    # i18n translation keys
    label_key = get_value_with_aliases(raw, "ui_label_key", "label_key")
    description_key = get_value_with_aliases(raw, "ui_description_key", "description_key")

    # The browser applies bundled translations through labelKey/descriptionKey.
    label, description = label_raw, description_raw

    # Visual properties
    icon_raw = get_value_with_aliases(raw, "ui_icon", "icon", default=defaults["icon"])
    color = get_value_with_aliases(raw, "ui_color", "color", default=defaults["color"])
    group = get_value_with_aliases(raw, "ui_group", default=f"{category.title()}")

    # Determine tier first, then derive visibility from tier for consistency
    # tier: internal (hidden), toolkit (expert), standard/featured (default)
    # NOTE: We ignore ui_visibility from source and always derive from tier
    # This ensures consistency across all normalizers (same as atomic.py)
    tier = raw.get("tier", "standard")
    if tier == "toolkit":
        visibility = "expert"
    elif tier == "internal":
        visibility = "hidden"
    else:
        visibility = "default"

    # Normalize icon to unified format
    icon = normalize_icon(icon_raw, color)

    # Process params_schema - Composite may use input_schema instead of params_schema
    params_schema_raw = get_value_with_aliases(
        raw,
        "ui_params_schema", "params_schema", "paramsSchema",
        "input_schema", "inputSchema",
        default={}
    )
    params_schema = normalize_params_schema(params_schema_raw)
    params_schema = add_hidden_markers(params_schema)

    # Pre-compute default params
    default_params = compute_default_params(params_schema)

    # Detect node type (default to 'composite')
    node_type = detect_node_type(module_id, raw) or "composite"

    # Detect AI flags
    ai_flags = detect_ai_module_flags(module_id, category, raw)

    # Detect if custom UI is needed
    requires_custom_ui = detect_requires_custom_ui(module_id, raw)

    # Output schema
    output_schema = get_value_with_aliases(raw, "output_schema", "outputSchema")

    # Source data for composite
    source_data = {
        "stepCount": len(raw.get("steps", [])),
    }

    # Create canonical module using factory function
    result = create_canonical_module(
        module_id=module_id,
        label=label,
        category=category,
        source="composite",

        # Display
        description=description,
        icon=icon,
        color=color,
        group=group,
        tier=tier,
        visibility=visibility,
        tags=raw.get("tags", []),
        labelKey=label_key,
        descriptionKey=description_key,

        # Schema
        paramsSchema=params_schema,
        defaultParams=default_params,
        outputSchema=output_schema,

        # Connection
        inputTypes=raw.get("input_types", []),
        outputTypes=raw.get("output_types", []),
        canReceiveFrom=raw.get("can_receive_from", []),
        canConnectTo=raw.get("can_connect_to", []),
        inputPorts=[convert_snake_to_camel(p) for p in raw.get("input_ports", [])],
        outputPorts=[convert_snake_to_camel(p) for p in raw.get("output_ports", [])],

        # Node
        nodeType=node_type,

        # AI flags
        isAIModel=ai_flags["isAIModel"],
        isMemory=ai_flags["isMemory"],
        isTool=ai_flags["isTool"],
        isTemplate=is_template_module(module_id),

        # UI flags
        requiresCustomUI=requires_custom_ui,

        # Execution
        timeout=raw.get("timeout"),
        retryable=raw.get("retryable", False),
        maxRetries=raw.get("max_retries", 3),
        concurrentSafe=raw.get("concurrent_safe", True),
        requiresCredentials=raw.get("requires_credentials", False),
        requiredPermissions=raw.get("required_permissions", []),

        # Metadata
        version=raw.get("version", "1.0.0"),
        stability=raw.get("stability", "stable"),
        author=raw.get("author"),
        docsUrl=raw.get("docs_url"),
        deprecated=raw.get("deprecated", False),
        isVerified=raw.get("is_verified", False),
        isFeatured=raw.get("is_featured", False),

        # Source data
        sourceData=source_data,
    )

    # Enrich with node configuration (uiConfig, inputHandles, outputHandles, dynamicHandles)
    result = enrich_module_with_node_config(result)

    # Add snake_case aliases if enabled for backward compatibility
    if INCLUDE_SNAKE_CASE_ALIASES:
        result = add_snake_case_aliases(result)

    return result
