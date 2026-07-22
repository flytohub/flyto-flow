"""
Template Schema Builder

Functions for building paramsSchema and outputSchema from template UI sections,
stored schemas, and module registry metadata.

Canonical location: services/template/schema_builder.py
Re-exported by api/templates/schema_builder.py for backward compatibility.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Schema Building Functions
# =============================================================================


def _infer_schema_from_input_type(lookup_type: str) -> str:
    """Map a normalized input type to its JSON schema type.

    Args:
        lookup_type: Normalized component type (lowercase, hyphens removed)
            or module-based type (e.g. 'form.number').

    Returns:
        JSON schema type string ('string', 'number', or 'boolean').
    """
    TYPE_MAP = {
        'input': 'string', 'text': 'string', 'textinput': 'string',
        'textarea': 'string', 'number': 'number', 'numberinput': 'number',
        'email': 'string', 'emailinput': 'string',
        'password': 'string', 'passwordinput': 'string',
        'url': 'string', 'urlinput': 'string',
        'tel': 'string', 'telinput': 'string',
        'select': 'string', 'selectinput': 'string',
        'checkbox': 'boolean', 'checkboxinput': 'boolean',
        'radio': 'string', 'radioinput': 'string',
        'switch': 'boolean', 'switchinput': 'boolean',
        'date': 'string', 'dateinput': 'string',
        'time': 'string', 'timeinput': 'string',
        'range': 'number', 'rangeinput': 'number',
        'rating': 'number', 'ratinginput': 'number',
        'file': 'string', 'fileinput': 'string',
        'color': 'string', 'colorinput': 'string', 'colorpicker': 'string',
        'forminput': 'string',
        # Module-based types
        'form.input': 'string', 'form.number': 'number', 'form.email': 'string',
        'form.password': 'string', 'form.url': 'string', 'form.tel': 'string',
        'form.textarea': 'string', 'form.select': 'string', 'form.checkbox': 'boolean',
        'form.radio': 'string', 'form.switch': 'boolean', 'form.date': 'string',
        'form.time': 'string', 'form.range': 'number', 'form.rating': 'number',
        'form.file': 'string',
        'form.color': 'string', 'form.input_color': 'string',
    }
    return TYPE_MAP.get(lookup_type, "string")


def _process_ui_component(comp: dict) -> tuple:
    """Process one UI component and return its schema property.

    Args:
        comp: A component dict from a UI section column.

    Returns:
        (key, prop, is_required) tuple if the component is a form input,
        or (None, None, False) if it should be skipped.
    """
    # Supported form component types (normalized: lowercase, hyphens removed)
    FORM_COMPONENTS = {
        'input', 'text', 'textinput', 'number', 'numberinput',
        'email', 'emailinput', 'password', 'passwordinput',
        'url', 'urlinput', 'tel', 'telinput',
        'textarea', 'select', 'selectinput',
        'checkbox', 'checkboxinput', 'radio', 'radioinput',
        'switch', 'switchinput', 'date', 'dateinput',
        'time', 'timeinput', 'range', 'rangeinput',
        'rating', 'ratinginput', 'file', 'fileinput',
        'color', 'colorinput', 'colorpicker',
        'forminput',
        # Module-based form components
        'form.input', 'form.number', 'form.email', 'form.password',
        'form.url', 'form.tel', 'form.textarea', 'form.select',
        'form.checkbox', 'form.radio', 'form.switch', 'form.date',
        'form.time', 'form.range', 'form.rating', 'form.file',
        'form.color', 'form.input_color',
    }

    # Direct UI component type for frontend rendering (SchemaField.vue)
    COMPONENT_TYPE_MAP = {
        'input': 'text', 'text': 'text', 'textinput': 'text',
        'textarea': 'textarea',
        'number': 'number', 'numberinput': 'number',
        'email': 'email', 'emailinput': 'email',
        'password': 'password', 'passwordinput': 'password',
        'url': 'url', 'urlinput': 'url',
        'tel': 'text', 'telinput': 'text',
        'select': 'select', 'selectinput': 'select',
        'checkbox': 'boolean', 'checkboxinput': 'boolean',
        'radio': 'select', 'radioinput': 'select',
        'switch': 'boolean', 'switchinput': 'boolean',
        'date': 'date', 'dateinput': 'date',
        'time': 'date', 'timeinput': 'date',
        'range': 'slider', 'rangeinput': 'slider',
        'rating': 'number', 'ratinginput': 'number',
        'file': 'fileUpload', 'fileinput': 'fileUpload',
        'color': 'color', 'colorinput': 'color', 'colorpicker': 'color',
        'forminput': 'text',
        # Module-based
        'form.input': 'text', 'form.number': 'number', 'form.email': 'email',
        'form.password': 'password', 'form.url': 'url', 'form.tel': 'text',
        'form.textarea': 'textarea', 'form.select': 'select',
        'form.checkbox': 'boolean', 'form.radio': 'select',
        'form.switch': 'boolean', 'form.date': 'date',
        'form.time': 'date', 'form.range': 'slider',
        'form.rating': 'number', 'form.file': 'fileUpload',
        'form.color': 'color', 'form.input_color': 'color',
    }

    SELECT_TYPES = {
        'select', 'selectinput', 'radio', 'radioinput',
        'form.select', 'form.radio',
    }

    # Normalize type: lowercase + remove hyphens
    comp_type = (comp.get("type") or "").lower().replace("-", "")
    comp_module = (comp.get("module") or "").lower()

    # Check if it's a form component by type or module
    is_form = comp_type in FORM_COMPONENTS or comp_module.startswith("form.")
    if not is_form:
        return None, None, False

    # Get parameter key (supports both naming conventions)
    params = comp.get("params", {})
    key = (
        params.get("variableName") or
        params.get("variable_name") or
        comp.get("id")
    )
    if not key or not key.strip():
        return None, None, False

    # Determine JSON schema type
    lookup_type = comp_module if comp_module.startswith("form.") else comp_type
    schema_type = _infer_schema_from_input_type(lookup_type)

    # Build property schema
    prop = {
        "type": schema_type,
        "label": comp.get("label") or params.get("label") or key,
    }

    # UI component type — frontend reads this directly
    if ct := COMPONENT_TYPE_MAP.get(lookup_type):
        prop["componentType"] = ct

    # Optional attributes
    if desc := (comp.get("description") or params.get("description")):
        prop["description"] = desc
    if placeholder := (comp.get("placeholder") or params.get("placeholder")):
        prop["placeholder"] = placeholder
    comp_default = comp.get("default")
    params_default = params.get("default")
    if comp_default is not None:
        prop["default"] = comp_default
    elif params_default is not None:
        prop["default"] = params_default
    if lookup_type in SELECT_TYPES:
        if options := (comp.get("options") or params.get("options")):
            prop["options"] = options

    # Required flag
    is_required = bool(comp.get("required") or params.get("required"))
    if is_required:
        prop["required"] = True

    return key, prop, is_required


def build_params_schema_from_ui(ui: dict) -> dict:
    """
    Build paramsSchema from Template UI sections.
    Called at save time and stored in the local CE database.

    This is the single source of truth for computing params_schema.
    Handles both snake_case and camelCase field names.
    Supports all component type formats: HTML types, Vue component names
    (PascalCase, camelCase, kebab-case), and form.* module prefixes.

    Args:
        ui: Template UI config with sections

    Returns:
        JSON Schema format paramsSchema
    """
    properties = {}
    required = []

    sections = ui.get("sections", []) if ui else []

    for section in sections:
        # Handle both snake_case and camelCase workflow formats.
        columns = section.get("columnsData") or section.get("columns_data") or []

        for column in columns:
            components = column.get("components", [])

            for comp in components:
                key, prop, is_required = _process_ui_component(comp)
                if key is None:
                    continue

                if is_required:
                    required.append(key)

                properties[key] = prop

    # Add template.invoke hidden parameters
    # Note: template_id and library_id should NOT have defaults - they are set dynamically
    # when the template is added as a node. Setting skipDefault=true prevents
    # compute_default_params from overwriting actual values with empty strings.
    properties["template_id"] = {"type": "string", "hidden": True, "skipDefault": True}
    properties["library_id"] = {"type": "string", "hidden": True, "skipDefault": True}
    properties["timeout_seconds"] = {"type": "number", "default": 300, "hidden": True}

    schema = {
        "type": "object",
        "properties": properties,
    }
    # Only include 'required' field if there are required properties
    # (JSON Schema doesn't allow null for 'required')
    if required:
        schema["required"] = required
    return schema


def build_params_schema_for_template(template: dict) -> dict:
    """
    Build paramsSchema for a template, checking all sources in priority order:
    1. Stored params_schema / paramsSchema (pre-computed at save time)
    2. input_schema (legacy format with properties)
    3. UI sections (computed dynamically via build_params_schema_from_ui)

    This replaces the deprecated compute_params_schema_for_template().

    Args:
        template: Local workflow-template dictionary

    Returns:
        JSON Schema format paramsSchema
    """
    # 1. Prefer stored params_schema
    stored = template.get("params_schema") or template.get("paramsSchema")
    if stored and isinstance(stored, dict) and stored.get("properties"):
        return stored

    # 2. Check legacy input_schema
    input_schema = template.get("input_schema")
    if input_schema and isinstance(input_schema, dict) and input_schema.get("properties"):
        properties = dict(input_schema.get("properties", {}))
        required = list(input_schema.get("required", []))

        # Add hidden template.invoke params
        properties["template_id"] = {"type": "string", "hidden": True, "skipDefault": True}
        properties["library_id"] = {"type": "string", "hidden": True, "skipDefault": True}
        properties["timeout_seconds"] = {"type": "number", "default": 300, "hidden": True}

        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema

    # 3. Compute from UI sections
    ui = template.get("ui", {})
    return build_params_schema_from_ui(ui)


def build_output_schema_from_steps(steps: list) -> dict:
    """
    Infer output_schema from the last step's module metadata.

    Called at save time — walks the steps list backwards to find the last
    non-error-handler step and looks up its output_schema from the
    flyto-core module registry.

    Returns:
        JSON Schema describing the template's output.
    """
    if not steps:
        return {"type": "object", "properties": {}}

    try:
        from services.registry_loader import get_module_registry
        registry = get_module_registry()
        if not registry:
            return {"type": "object", "properties": {}}

        all_metadata = registry.get_all_metadata()

        # Walk backwards to find the last meaningful step
        for step in reversed(steps):
            module_id = step.get("module") or step.get("moduleId") or ""

            # Skip error triggers / flow control — they're not real outputs
            if module_id.startswith("flow.") or module_id.startswith("error."):
                continue

            # If step already has an explicit outputSchema, use it
            step_output = step.get("outputSchema") or step.get("output_schema")
            if step_output and step_output.get("properties"):
                return step_output

            # For template.invoke steps, use generic object (nested templates)
            if module_id.startswith("template."):
                return {"type": "object", "properties": {}}

            # Look up module's output_schema from registry
            meta = all_metadata.get(module_id, {})
            output_schema = meta.get("output_schema") or meta.get("outputSchema")
            if output_schema and isinstance(output_schema, dict):
                # Strip internal keys (__ prefix)
                return {k: v for k, v in output_schema.items() if not k.startswith("__")}

            # Found a real step but no schema — return generic
            return {"type": "object", "properties": {}}

    except Exception as e:
        logger.warning(f"Failed to infer output_schema from steps: {e}")

    return {"type": "object", "properties": {}}
