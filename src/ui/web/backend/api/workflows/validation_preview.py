"""
Workflow Preview Schema

Compute preview input schema from workflow and UI components.
"""

import re
from typing import Dict, List, Any


def compute_preview_schema(workflow_elements: List[Dict[str, Any]], ui_sections: List[Dict[str, Any]]) -> dict:
    """
    Compute preview input schema from workflow and UI components.

    S-Grade: All schema inference on backend.

    Args:
        workflow_elements: VueFlow nodes/edges
        ui_sections: UI tab sections with components

    Returns:
        {
            "merged_schema": {...},
            "ui_fields": [...],
            "inferred_fields": [...],
            "workflow_refs": [...],
            "workflow_steps": [...]
        }
    """
    # Form types that are input components
    FORM_TYPES = [
        'input', 'number', 'email', 'password', 'url', 'tel',
        'textarea', 'select', 'checkbox', 'radio', 'switch',
        'date', 'time', 'range', 'rating', 'file'
    ]

    # Component type to schema type mapping
    TYPE_MAP = {
        'input': 'string', 'textarea': 'string', 'number': 'number',
        'email': 'string', 'password': 'string', 'url': 'string',
        'tel': 'string', 'select': 'string', 'checkbox': 'boolean',
        'radio': 'string', 'switch': 'boolean', 'date': 'string',
        'time': 'string', 'range': 'number', 'rating': 'number', 'file': 'file'
    }

    # Extract variable references from workflow params
    workflow_refs = set()
    nodes = [el for el in workflow_elements if el.get("id") and not el.get("source")]
    patterns = [
        re.compile(r'\$\{ui\.(\w+)\}'),
        re.compile(r'\{\{\s*ui\.(\w+)\s*\}\}'),
        re.compile(r'\{\{\s*inputs\.(\w+)\s*\}\}')
    ]

    for node in nodes:
        params = node.get("data", {}).get("params", {})
        for value in params.values():
            if isinstance(value, str):
                for pattern in patterns:
                    for match in pattern.finditer(value):
                        workflow_refs.add(match.group(1))

    # Extract UI form inputs
    ui_fields = []
    for section in ui_sections:
        columns_data = section.get("columns_data", [])
        for col in columns_data:
            components = col.get("components", [])
            for comp in components:
                comp_type = comp.get("type", "")
                comp_module = comp.get("module", "")
                is_form = comp_module.startswith("form.") or comp_type in FORM_TYPES

                if is_form:
                    params = comp.get("params", {})
                    key = params.get("variable_name") or comp.get("id", "")
                    schema = _build_schema_from_component(comp, TYPE_MAP)

                    ui_fields.append({
                        "key": key,
                        "label": comp.get("label") or params.get("label") or key,
                        "type": comp_type,
                        "schema": schema,
                        "source": "ui"
                    })

    # Auto-infer inputs not defined in UI
    ui_keys = {f["key"] for f in ui_fields}
    inferred_fields = []

    for var_name in workflow_refs:
        if var_name not in ui_keys:
            label = _format_label(var_name)
            inferred_fields.append({
                "key": var_name,
                "label": label,
                "type": "string",
                "schema": {
                    "type": "string",
                    "label": label,
                    "placeholder": f"Enter {label.lower()}"
                },
                "source": "auto-inferred"
            })

    # Merge schema (UI takes priority)
    merged_schema = {}
    for field in ui_fields:
        merged_schema[field["key"]] = field["schema"]
    for field in inferred_fields:
        if field["key"] not in merged_schema:
            merged_schema[field["key"]] = field["schema"]

    # Workflow steps for progress display
    workflow_steps = [
        {
            "id": node.get("id"),
            "index": i,
            "label": node.get("data", {}).get("label") or node.get("id"),
            "module": node.get("data", {}).get("module")
        }
        for i, node in enumerate(nodes)
    ]

    return {
        "merged_schema": merged_schema,
        "ui_fields": ui_fields,
        "inferred_fields": inferred_fields,
        "workflow_refs": list(workflow_refs),
        "workflow_steps": workflow_steps
    }


def _build_schema_from_component(comp: dict, type_map: dict) -> dict:
    """Build schema from UI component"""
    comp_type = comp.get("type", "input")
    schema = {
        "type": type_map.get(comp_type, "string"),
        "label": comp.get("label") or comp.get("params", {}).get("label") or comp.get("id", "")
    }

    if comp.get("required"):
        schema["required"] = True
    if comp.get("default") is not None:
        schema["default"] = comp["default"]
    if comp.get("placeholder"):
        schema["placeholder"] = comp["placeholder"]

    # Select/Radio options
    if comp_type in ("select", "radio") and comp.get("options"):
        schema["options"] = comp["options"]

    # Range slider
    if comp_type == "range":
        schema["min"] = comp.get("min", 0)
        schema["max"] = comp.get("max", 100)
        schema["step"] = comp.get("step", 1)

    # Number constraints
    if comp_type == "number":
        if comp.get("min") is not None:
            schema["min"] = comp["min"]
        if comp.get("max") is not None:
            schema["max"] = comp["max"]

    # Textarea
    if comp_type == "textarea" and comp.get("rows"):
        schema["format"] = "multiline"

    # File accept
    if comp_type == "file" and comp.get("accept"):
        schema["accept"] = comp["accept"]

    return schema


def _format_label(key: str) -> str:
    """Format variable name as human-readable label"""
    label = re.sub(r'_', ' ', key)
    label = re.sub(r'([a-z])([A-Z])', r'\1 \2', label)
    return label.capitalize()
