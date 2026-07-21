"""
Atomic Module Adapter

Converts raw atomic module metadata from flyto-core registry to CanonicalModule format.
"""

from typing import Dict, Any, Optional

from config.constants import CATEGORY_DEFAULTS, DEFAULT_CATEGORY_META
from services.template.schemas.canonical_module import (
    CanonicalModule,
    create_canonical_module,
    add_snake_case_aliases,
    convert_snake_to_camel,
    INCLUDE_SNAKE_CASE_ALIASES,
)
from services.node_config import enrich_module_with_node_config
from services.i18n_service import translate, translate_module
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


def normalize_atomic(raw: Dict[str, Any], level: str = "atomic", lang: str = "en") -> CanonicalModule:
    """
    Convert atomic module metadata to CanonicalModule format.

    Input comes from: registry_loader.py -> get_module_registry().get_all_metadata()

    Args:
        raw: Raw metadata from flyto-core registry
        level: Module level (default "atomic")
        lang: Language code for i18n translation (default "en")

    Returns:
        CanonicalModule with all fields populated
    """
    # Extract module ID
    module_id = get_value_with_aliases(raw, "module_id", "moduleId", default="unknown")
    category = raw.get("category", module_id.split(".")[0])
    defaults = get_category_meta(category)

    # Display fields (original English)
    label_raw = get_value_with_aliases(raw, "ui_label", "label", default=module_id)
    description_raw = get_value_with_aliases(raw, "ui_description", "description", default="")

    # i18n translation keys
    label_key = get_value_with_aliases(raw, "ui_label_key", "label_key")
    description_key = get_value_with_aliases(raw, "ui_description_key", "description_key")

    # Apply i18n translation if lang is not English
    label, description = translate_module(
        label=label_raw,
        description=description_raw,
        label_key=label_key,
        description_key=description_key,
        locale=lang
    )
    icon_raw = get_value_with_aliases(raw, "ui_icon", "icon", default=defaults["icon"])
    color = get_value_with_aliases(raw, "ui_color", "color", default=defaults["color"])
    group = get_value_with_aliases(raw, "ui_group", default=f"{category.title()}")

    # Determine tier first, then set visibility based on tier
    # tier: internal (hidden), toolkit (expert), standard/featured (default)
    # NOTE: We ignore ui_visibility from core because it's inconsistent with tier
    # (67 modules have tier=standard but ui_visibility=expert)
    # Visibility should always be derived from tier for consistency
    tier = raw.get("tier", "standard")
    if tier == "toolkit":
        visibility = "expert"
    elif tier == "internal":
        visibility = "hidden"
    else:
        visibility = "default"

    # Normalize icon to unified format
    icon = normalize_icon(icon_raw, color)

    # Process params_schema
    params_schema_raw = get_value_with_aliases(
        raw, "ui_params_schema", "params_schema", "paramsSchema", default={}
    )
    # Build translate function for param labels (skip for English)
    param_translate_fn = (lambda key, fallback: translate(key, lang, fallback)) if lang != "en" else None
    params_schema = normalize_params_schema(params_schema_raw, translate_fn=param_translate_fn)
    params_schema = add_hidden_markers(params_schema)

    # Pre-compute default params
    default_params = compute_default_params(params_schema)

    # Detect node type
    node_type = detect_node_type(module_id, raw) or defaults.get("nodeType", "standard")

    # Detect AI flags
    ai_flags = detect_ai_module_flags(module_id, category, raw)

    # Detect if custom UI is needed
    requires_custom_ui = detect_requires_custom_ui(module_id, raw)

    # Output schema
    output_schema = get_value_with_aliases(raw, "output_schema", "outputSchema")

    # Create canonical module using factory function
    result = create_canonical_module(
        module_id=module_id,
        label=label,
        category=category,
        source="atomic",

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
        isVerified=True,  # Atomic modules are always verified
        isFeatured=raw.get("is_featured", False),

        # Source data (empty for atomic)
        sourceData={},
    )

    # Enrich with node configuration (uiConfig, inputHandles, outputHandles, dynamicHandles)
    result = enrich_module_with_node_config(result)

    # Add snake_case aliases if enabled for backward compatibility
    if INCLUDE_SNAKE_CASE_ALIASES:
        result = add_snake_case_aliases(result)

    return result
