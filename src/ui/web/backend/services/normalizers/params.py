"""
Parameter Schema Normalization Utilities

Functions for normalizing parameter schemas, detecting component types,
and handling default values and hidden markers.
"""

from typing import Dict, Any, Callable, List


# Field names that should always render as textarea
_TEXTAREA_FIELD_NAMES = frozenset({
    # Prompts & AI
    "prompt", "system_prompt", "user_prompt", "assistant_prompt",
    "instructions", "system_message",
    # Content
    "body", "content", "text", "message", "description",
    "html_content", "markdown", "raw_text",
    # Code
    "code", "script", "command", "commands",
    "query", "sql", "graphql", "xpath", "css_selector",
    "expression", "formula", "regex", "pattern",
    # Templates
    "template", "template_string", "jinja_template",
    # Data
    "json_data", "yaml_data", "xml_data", "csv_data",
    "payload", "request_body", "response_body",
    # Config
    "config", "configuration", "manifest",
    "private_key", "public_key", "certificate",
    # Other
    "notes", "comment", "remarks", "summary",
    "old_string", "new_string", "original", "modified",
})

# Suffixes that indicate textarea
_TEXTAREA_FIELD_SUFFIXES = (
    "_prompt", "_template", "_body", "_content",
    "_code", "_script", "_query", "_text",
    "_message", "_instructions", "_command",
)


def _translate_options(options: list, translate_fn=None) -> list:
    """Translate option labels if they have label_key."""
    if not translate_fn or not isinstance(options, list):
        return options
    result = []
    for opt in options:
        if isinstance(opt, dict) and opt.get("label_key"):
            opt = {**opt, "label": translate_fn(opt["label_key"], opt.get("label", opt.get("value", "")))}
            result.append(opt)
        else:
            result.append(opt)
    return result


def normalize_params_schema(raw: Any, translate_fn=None) -> Dict[str, Any]:
    """
    Normalize any params schema input to standard JSON Schema format.

    Input handling:
    1. flyto params_schema dict -> standardize structure
    2. JSON Schema (from plugins) -> ensure proper format
    3. input_schema (legacy) -> merge into params_schema
    4. None -> empty schema
    5. Array format (legacy) -> convert to object format

    Output format (standard JSON Schema):
    {
        "type": "object",
        "properties": {
            "param_name": {
                "type": "string",
                "label": "...",
                "description": "...",
                "default": "...",
                "hidden": false
            }
        },
        "required": ["..."]
    }

    Args:
        raw: Raw schema in any supported format
        translate_fn: Optional callable(key, fallback) -> str for i18n translation

    Returns:
        Standardized JSON Schema object
    """
    if not raw:
        return {"type": "object", "properties": {}, "required": []}

    # Dict input
    if isinstance(raw, dict):
        if "properties" in raw:
            # Has explicit properties key (with or without "type": "object")
            properties = {k: _normalize_param_property(v, translate_fn, field_name=k) for k, v in raw.get("properties", {}).items()}
        else:
            # Direct properties dict (keys are param names)
            properties = {k: _normalize_param_property(v, translate_fn, field_name=k) for k, v in raw.items() if k not in ("type", "required")}
        return {
            "type": "object",
            "properties": properties,
            "required": raw.get("required") or []
        }

    # Array format (legacy)
    if isinstance(raw, list):
        properties = {}
        required = []
        for item in raw:
            if isinstance(item, dict):
                key = item.get("name") or item.get("key") or item.get("id")
                if key:
                    properties[key] = _normalize_param_property(item, translate_fn, field_name=key)
                    if item.get("required"):
                        required.append(key)
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    # Fallback
    return {"type": "object", "properties": {}, "required": []}


def _convert_conditions(raw_conditions: Dict) -> Dict:
    """Convert showIf/hideIf conditions to displayOptions format."""
    result = {}
    for field_name, condition in raw_conditions.items():
        if isinstance(condition, dict):
            result[field_name] = condition["$in"] if "$in" in condition else condition
        elif isinstance(condition, list):
            result[field_name] = condition
        else:
            result[field_name] = [condition]
    return result


# Widget name → component type (explicit hints from flyto-core field() builder)
_WIDGET_MAP = {
    "element_picker": "elementPicker",
    "textarea": "textarea",
    "text_area": "textarea",
    "json_editor": "jsonEditor",
    "auth_config": "authConfig",
    "key_value": "keyValue",
    "multiselect": "multiselect",
}

# Format string → component type
_FORMAT_MAP = {
    "json": "jsonEditor",
    "file": "fileUpload",
    "image": "imageUpload",
    "password": "password",
    "path": "path",
    "url": "url",
    "email": "email",
    "color": "color",
    "date": "date",
    "datetime": "datetime",
    "multiline": "textarea",
    "text": "textarea",
}


def _detect_component_type(prop: Dict[str, Any], field_name: str = "") -> str:
    """
    Detect the UI component type for a normalized parameter property.

    Backend is single source of truth -- frontend renders whatever we return.
    Order matters: first match wins.

    Returns one of the KNOWN_COMPONENT_TYPES:
        text, number, email, password, url, color, date, datetime,
        textarea, path, select, boolean, slider, fileUpload, imageUpload,
        authConfig, keyValue, nestedObject, array, jsonEditor, multiselect,
        elementPicker
    """
    widget = prop.get("widget", "")
    ui_widget = (prop.get("ui") or {}).get("widget", "") if isinstance(prop.get("ui"), dict) else ""
    prop_type = prop.get("type", "string")
    fmt = prop.get("format", "")

    # 1. Widget-based (explicit hint)
    for w in (widget, ui_widget):
        if w in _WIDGET_MAP:
            return _WIDGET_MAP[w]

    # Multiselect also matches on prop_type
    if prop_type == "multiselect":
        return "multiselect"

    # json format → jsonEditor (before format map, since widget check already passed)
    if fmt == "json":
        return "jsonEditor"

    # 2. Options/enum → select
    options = prop.get("options")
    enum = prop.get("enum")
    if (options and isinstance(options, list) and len(options) > 0) or \
       (enum and isinstance(enum, list) and len(enum) > 0):
        return "select"

    # 3. Type-based
    if prop_type == "array":
        return "array"
    if prop_type == "boolean":
        return "boolean"
    if prop_type == "object":
        properties = prop.get("properties")
        if properties and isinstance(properties, dict) and len(properties) > 0:
            return "nestedObject"
        return "keyValue"

    # 4. Format-based
    if fmt in _FORMAT_MAP:
        return _FORMAT_MAP[fmt]

    # 5. Number with min+max → slider, otherwise number
    if prop_type in ("number", "integer"):
        if prop.get("minimum") is not None and prop.get("maximum") is not None:
            return "slider"
        return "number"

    # 6. Name-based heuristic for common long-text fields (string type only)
    if prop_type in ("string", "text"):
        name_lower = field_name.lower()
        if name_lower in _TEXTAREA_FIELD_NAMES:
            return "textarea"
        for suffix in _TEXTAREA_FIELD_SUFFIXES:
            if name_lower.endswith(suffix):
                return "textarea"
        default = prop.get("default", "")
        if isinstance(default, str) and len(default) > 80:
            return "textarea"

    return "text"


def _extract_base_fields(prop: Dict[str, Any], translate_fn) -> Dict[str, Any]:
    prop_type = prop.get("type", "string")
    if isinstance(prop_type, list):
        prop_type = prop_type[0] if prop_type else "any"

    label = prop.get("label", "")
    description = prop.get("description", "")

    if translate_fn:
        label_key = prop.get("label_key")
        desc_key = prop.get("description_key")
        if label_key:
            label = translate_fn(label_key, label)
        if desc_key:
            description = translate_fn(desc_key, description)

    return {
        "type": prop_type,
        "label": label,
        "description": description,
    }


def _extract_optional_fields(prop: Dict[str, Any], result: Dict[str, Any], translate_fn) -> None:
    if prop.get("default") is not None:
        result["default"] = prop["default"]
    if prop.get("placeholder"):
        result["placeholder"] = prop["placeholder"]
    if prop.get("required"):
        result["required"] = True
    if prop.get("hidden"):
        result["hidden"] = True
    if prop.get("options"):
        result["options"] = _translate_options(prop["options"], translate_fn)
    if prop.get("enum"):
        result["enum"] = prop["enum"]
    if prop.get("minimum") is not None:
        result["minimum"] = prop["minimum"]
    if prop.get("maximum") is not None:
        result["maximum"] = prop["maximum"]

    validation = prop.get("validation")
    if validation and isinstance(validation, dict):
        if validation.get("min") is not None and "minimum" not in result:
            result["minimum"] = validation["min"]
        if validation.get("max") is not None and "maximum" not in result:
            result["maximum"] = validation["max"]

    if prop.get("step") is not None:
        result["step"] = prop["step"]
    if prop.get("minLength") is not None:
        result["minLength"] = prop["minLength"]
    if prop.get("maxLength") is not None:
        result["maxLength"] = prop["maxLength"]
    if prop.get("format"):
        result["format"] = prop["format"]
    if prop.get("pathMode"):
        result["pathMode"] = prop["pathMode"]
    if prop.get("pattern"):
        result["pattern"] = prop["pattern"]

    if prop.get("secret") and not result.get("format"):
        result["format"] = "password"


def _extract_nested_schemas(prop: Dict[str, Any], result: Dict[str, Any], translate_fn) -> None:
    if prop.get("properties") and isinstance(prop["properties"], dict):
        normalized_props = {}
        for k, v in prop["properties"].items():
            normalized_props[k] = _normalize_param_property(v, translate_fn, field_name=k)
        result["properties"] = normalized_props

    if prop.get("items") and isinstance(prop["items"], dict):
        result["items"] = _normalize_param_property(prop["items"], translate_fn)
    if prop.get("minItems") is not None:
        result["minItems"] = prop["minItems"]
    if prop.get("maxItems") is not None:
        result["maxItems"] = prop["maxItems"]


def _extract_display_options(prop: Dict[str, Any], result: Dict[str, Any]) -> None:
    if prop.get("displayOptions"):
        result["displayOptions"] = prop["displayOptions"]

    if prop.get("showIf") or prop.get("hideIf"):
        display_opts = result.get("displayOptions", {})
        if prop.get("showIf"):
            display_opts["show"] = _convert_conditions(prop["showIf"])
        if prop.get("hideIf"):
            display_opts["hide"] = _convert_conditions(prop["hideIf"])
        result["displayOptions"] = display_opts

    if prop.get("show_when"):
        result["showWhen"] = prop["show_when"]
    if prop.get("showWhen"):
        result["showWhen"] = prop["showWhen"]


def _extract_widget_hints(prop: Dict[str, Any], result: Dict[str, Any]) -> None:
    if prop.get("widget"):
        result["widget"] = prop["widget"]
    if prop.get("ui") and isinstance(prop.get("ui"), dict):
        if prop["ui"].get("widget"):
            result["widget"] = prop["ui"]["widget"]
        result["ui"] = prop["ui"]


def _extract_visibility(prop: Dict[str, Any], result: Dict[str, Any]) -> None:
    if prop.get("visibility"):
        result["visibility"] = prop["visibility"]
    if prop.get("advanced"):
        result["advanced"] = prop["advanced"]
    elif prop.get("group") == "advanced":
        result["advanced"] = True


_NORMALIZATION_PIPELINE: List[Callable] = [
    lambda prop, result, translate_fn: _extract_optional_fields(prop, result, translate_fn),
    lambda prop, result, translate_fn: _extract_nested_schemas(prop, result, translate_fn),
    lambda prop, result, translate_fn: _extract_display_options(prop, result),
    lambda prop, result, translate_fn: _extract_widget_hints(prop, result),
    lambda prop, result, translate_fn: _extract_visibility(prop, result),
]


def _normalize_param_property(prop: Any, translate_fn=None, field_name: str = "") -> Dict[str, Any]:
    """
    Normalize a single parameter property.

    Args:
        prop: Raw parameter property dict
        translate_fn: Optional callable(key, fallback) -> str for i18n translation
        field_name: Field name for heuristic widget detection (e.g. "prompt" -> textarea)

    Supports displayOptions for conditional field visibility (n8n-style):
    {
        "displayOptions": {
            "show": {"fieldName": ["value1", "value2"]},
            "hide": {"fieldName": ["value3"]}
        }
    }
    """
    if not isinstance(prop, dict):
        return {"type": "string"}

    result = _extract_base_fields(prop, translate_fn)

    for step in _NORMALIZATION_PIPELINE:
        step(prop, result, translate_fn)

    result["componentType"] = _detect_component_type(result, field_name)

    return result


def compute_default_params(params_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pre-compute default parameter values from schema.

    Backend is single source of truth - frontend uses this directly
    without computing defaults from schema.

    Args:
        params_schema: Parameter schema dict (already normalized)

    Returns:
        Dict of parameter name -> default value
    """
    if not params_schema:
        return {}

    defaults = {}
    properties = params_schema.get("properties", {})

    if not isinstance(properties, dict):
        return {}

    for key, prop in properties.items():
        if not isinstance(prop, dict):
            continue

        # Skip if skipDefault is set (e.g., template_id, library_id)
        # These should be set dynamically, not from defaults
        if prop.get("skipDefault"):
            continue

        # Use explicit default if defined
        if prop.get("default") is not None:
            defaults[key] = prop["default"]
        else:
            # Type-based defaults
            prop_type = prop.get("type", "")
            # Handle union types (list of types) - use first type
            if isinstance(prop_type, list):
                prop_type = prop_type[0] if prop_type else ""
            type_defaults = {
                "string": "",
                "number": 0,
                "integer": 0,
                "boolean": False,
                "array": [],
            }
            if prop_type in type_defaults:
                defaults[key] = type_defaults[prop_type]
            # Skip null/unknown types - let frontend handle missing keys

    return defaults


def add_hidden_markers(params_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure params_schema has hidden markers for internal fields.

    Backend marks hidden fields explicitly so frontend doesn't need conventions.

    Args:
        params_schema: Normalized params schema

    Returns:
        Schema with hidden: true added to internal fields
    """
    if not params_schema or not isinstance(params_schema, dict):
        return params_schema

    # Hidden field patterns - these are internal and shouldn't be shown in UI
    hidden_patterns = {
        "template_id", "templateId", "library_id", "libraryId",
        "timeout_seconds", "_internal", "_context", "_session_id",
        "model_id", "modelId"
    }

    result = dict(params_schema)
    properties = result.get("properties", {})

    if isinstance(properties, dict):
        result["properties"] = {}
        for key, prop in properties.items():
            prop_copy = dict(prop) if isinstance(prop, dict) else {"type": "string"}

            # Mark as hidden if matches pattern or starts with underscore
            if key in hidden_patterns or key.startswith("_"):
                prop_copy["hidden"] = True

            result["properties"][key] = prop_copy

    return result
