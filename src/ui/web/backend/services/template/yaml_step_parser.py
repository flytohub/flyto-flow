"""
Step-level parsing and schema conversion for template YAML.
"""

import re
from typing import Any, Dict, List

# Sensitive parameter patterns — reuse the same list from api/templates.py
_SENSITIVE_PARAM_PATTERNS = [
    r'.*api[_-]?key.*',
    r'.*secret.*',
    r'.*password.*',
    r'.*token.*',
    r'.*credential.*',
    r'.*auth.*',
    r'.*private[_-]?key.*',
]
_SENSITIVE_RE = re.compile('|'.join(_SENSITIVE_PARAM_PATTERNS), re.IGNORECASE)

# UI-only step keys that should be separated into _ui
_UI_STEP_KEYS = {"position_x", "position_y", "pinned_output", "ui_state"}


def _sanitize_param_value(key: str, value: Any) -> Any:
    """Replace hardcoded secrets with env-variable placeholders."""
    if not isinstance(value, str):
        return value
    if value.startswith('${'):
        return value
    if _SENSITIVE_RE.match(key):
        env_name = re.sub(r'[^A-Z0-9]', '_', key.upper())
        return f'${{env.{env_name}}}'
    return value


def _sanitize_step_params(params: dict) -> dict:
    """Sanitize sensitive values in step params."""
    if not params or not isinstance(params, dict):
        return params
    return {k: _sanitize_param_value(k, v) for k, v in params.items()}


def _args_to_params_schema(args_def: Dict[str, Any]) -> Dict[str, Any]:
    """Convert YAML args definition to JSON Schema params_schema.

    YAML format:
        args:
          webhook_url:
            type: string
            required: true
            default: https://...
            description: Webhook URL

    Output JSON Schema:
        {
            "type": "object",
            "properties": {
                "webhook_url": {
                    "type": "string",
                    "default": "https://...",
                    "description": "Webhook URL"
                }
            },
            "required": ["webhook_url"]
        }
    """
    properties = {}
    required = []

    for arg_name, arg_def in args_def.items():
        if not isinstance(arg_def, dict):
            # Simple value like `count: 5` → treat as default
            properties[arg_name] = {"type": "string", "default": arg_def}
            continue

        prop: Dict[str, Any] = {}

        # Type mapping (YAML type → JSON Schema type)
        yaml_type = arg_def.get("type", "string")
        type_map = {"string": "string", "number": "number", "integer": "integer", "boolean": "boolean"}
        prop["type"] = type_map.get(yaml_type, "string")

        if "default" in arg_def:
            prop["default"] = arg_def["default"]
        if "description" in arg_def:
            prop["description"] = arg_def["description"]

        # Extended properties — preserves full fidelity in roundtrip
        if "label" in arg_def:
            prop["label"] = arg_def["label"]
        if "placeholder" in arg_def:
            prop["placeholder"] = arg_def["placeholder"]
        if "format" in arg_def:
            prop["format"] = arg_def["format"]
        if "options" in arg_def:
            prop["enum"] = arg_def["options"]
        elif "enum" in arg_def:
            prop["enum"] = arg_def["enum"]
        if "min" in arg_def:
            prop["minimum"] = arg_def["min"]
        elif "minimum" in arg_def:
            prop["minimum"] = arg_def["minimum"]
        if "max" in arg_def:
            prop["maximum"] = arg_def["max"]
        elif "maximum" in arg_def:
            prop["maximum"] = arg_def["maximum"]
        if "pattern" in arg_def:
            prop["pattern"] = arg_def["pattern"]

        properties[arg_name] = prop

        if arg_def.get("required"):
            required.append(arg_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _params_schema_to_args(params_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert JSON Schema params_schema back to YAML args format.

    Input JSON Schema:
        {
            "type": "object",
            "properties": {
                "webhook_url": {
                    "type": "string",
                    "default": "https://...",
                    "description": "Webhook URL"
                }
            },
            "required": ["webhook_url"]
        }

    Output YAML args:
        webhook_url:
          type: string
          required: true
          default: https://...
          description: Webhook URL
    """
    properties = params_schema.get("properties", {})
    required_list = set(params_schema.get("required", []))

    if not properties:
        return {}

    args: Dict[str, Any] = {}
    for name, prop in properties.items():
        if not isinstance(prop, dict):
            continue

        arg: Dict[str, Any] = {}
        arg["type"] = prop.get("type", "string")

        if name in required_list:
            arg["required"] = True

        if "default" in prop:
            arg["default"] = prop["default"]
        if "description" in prop:
            arg["description"] = prop["description"]

        # Extended properties — preserves full fidelity in roundtrip
        if "label" in prop:
            arg["label"] = prop["label"]
        if "placeholder" in prop:
            arg["placeholder"] = prop["placeholder"]
        if "format" in prop:
            arg["format"] = prop["format"]
        if "enum" in prop:
            arg["options"] = prop["enum"]
        if "minimum" in prop:
            arg["min"] = prop["minimum"]
        if "maximum" in prop:
            arg["max"] = prop["maximum"]
        if "pattern" in prop:
            arg["pattern"] = prop["pattern"]

        args[name] = arg

    return args


def _normalize_ui_components(ui: Dict[str, Any]) -> None:
    """Normalize UI builder components for frontend compatibility.

    YAML community templates may nest inputType, placeholder inside params,
    but the frontend builder expects them at the component top level.
    This flattens those fields so InputPreview renders correctly.
    """
    sections = ui.get("sections") if ui else None
    if not sections:
        return

    # Fields that the builder stores at component level, not under params
    _FLATTEN_FIELDS = ("inputType", "placeholder", "default", "required")

    for section in sections:
        for col in (section.get("columnsData") or []):
            for comp in (col.get("components") or []):
                params = comp.get("params")
                if not isinstance(params, dict):
                    params = {}
                for field in _FLATTEN_FIELDS:
                    if field in params and params[field] not in (None, ''):
                        if field not in comp or comp.get(field) in (None, ''):
                            comp[field] = params[field]

                # Hoist options from props into component top level
                # Frontend SchemaField reads field.options, not props.options
                props = comp.get("props")
                if isinstance(props, dict) and props.get("options"):
                    if not comp.get("options"):
                        comp["options"] = props["options"]
