"""
Template Module Adapter

Converts user template data to CanonicalModule format.
Templates are workflows that can be invoked as modules.
"""

import re
import logging
from typing import Dict, Any, List, Set

from services.template.schemas.canonical_module import (
    CanonicalModule,
    create_canonical_module,
    add_snake_case_aliases,
    INCLUDE_SNAKE_CASE_ALIASES,
)
from services.node_config import enrich_module_with_node_config
from services.module_id import generate_module_id
from .base import (
    normalize_icon,
    normalize_params_schema,
    compute_default_params,
    add_hidden_markers,
    detect_requires_custom_ui,
    get_value_with_aliases,
)

logger = logging.getLogger(__name__)


def extract_variables_from_steps(steps: List[Dict[str, Any]]) -> Set[str]:
    """
    Recursively extract ${xxx} variable references from all steps.

    Args:
        steps: List of template steps

    Returns:
        Set of variable names (excluding special variables)
    """
    def extract_from_obj(obj, variables: set):
        """Recursively extract ${xxx} variable references from any object."""
        if isinstance(obj, str):
            # Match ${variable} or ${variable.path}
            matches = re.findall(r'\$\{([a-zA-Z_][a-zA-Z0-9_]*)', obj)
            for var in matches:
                # Skip special variables
                if var not in ('secrets', 'env', 'context', 'steps', 'inputs', 'outputs'):
                    variables.add(var)
        elif isinstance(obj, dict):
            for v in obj.values():
                extract_from_obj(v, variables)
        elif isinstance(obj, list):
            for item in obj:
                extract_from_obj(item, variables)

    all_variables = set()
    for step in steps:
        step_params = step.get("params", {})
        extract_from_obj(step_params, all_variables)

    return all_variables


def extract_permissions_from_steps(steps: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    """
    Extract permissions, secrets, and capabilities from template steps.

    Args:
        steps: List of template steps

    Returns:
        Dict with permissions, required_secrets, side_effects, provides, consumes
    """
    permissions = set()
    required_secrets = set()
    side_effects = set()
    provides_capabilities = set()
    consumes_capabilities = set()

    for step in steps:
        step_module = step.get("module") or step.get("moduleId") or ""

        # Extract permissions based on module category
        if step_module.startswith("http.") or step_module.startswith("api."):
            permissions.add("network")
            side_effects.add("network.request")
            consumes_capabilities.add("network")
        if step_module.startswith("browser."):
            permissions.add("browser")
            permissions.add("network")
            side_effects.add("browser.automation")
            consumes_capabilities.add("browser")
        if step_module.startswith("file.") or step_module.startswith("fs."):
            permissions.add("filesystem")
            side_effects.add("filesystem.access")
        if step_module.startswith("db.") or step_module.startswith("database."):
            permissions.add("database")
            side_effects.add("database.query")
            consumes_capabilities.add("data.store")
        if step_module.startswith("llm.") or step_module.startswith("ai."):
            permissions.add("ai")
            permissions.add("network")
            consumes_capabilities.add("ai.infer")
        if step_module.startswith("line.") or step_module.startswith("telegram.") or step_module.startswith("slack."):
            permissions.add("network")
            permissions.add("messaging")
            side_effects.add("message.send")
            consumes_capabilities.add("message.send")
            provides_capabilities.add("message.receive")
        if step_module.startswith("notify.") or step_module.startswith("email."):
            permissions.add("network")
            side_effects.add("notify.send")

        # Extract required secrets from step params
        step_params = step.get("params", {})
        for key, value in step_params.items():
            if isinstance(value, str):
                # Match ${secrets.NAME} pattern
                secret_matches = re.findall(r'\$\{secrets\.([^}]+)\}', value)
                for secret_name in secret_matches:
                    # Only take the first part if it's a path like api_key.sub
                    base_secret = secret_name.split('.')[0] if '.' in secret_name else secret_name
                    required_secrets.add(base_secret)

        # Check step's own permissions declaration
        if step.get("permissions"):
            permissions.update(step.get("permissions"))
        if step.get("requiredSecrets"):
            required_secrets.update(step.get("requiredSecrets"))

    return {
        'permissions': permissions,
        'required_secrets': required_secrets,
        'side_effects': side_effects,
        'provides': provides_capabilities,
        'consumes': consumes_capabilities,
    }


def _convert_input_port(p: dict, template_id: str) -> dict:
    """Convert a core input port dict to camelCase frontend format."""
    port = {
        "id": p["id"],
        "handleId": p.get("handle_id", "target"),
        "position": p.get("position", "left"),
        "label": p.get("label", "Input"),
        "labelKey": f"templates.{template_id}.ports.{p['id']}",
        "dataType": p.get("data_type", "any"),
        "edgeType": p.get("edge_type", "data"),
    }
    if p.get("max_connections") is not None:
        port["maxConnections"] = p["max_connections"]
    if p.get("required") is not None:
        port["required"] = p["required"]
    return port


def _convert_output_port(p: dict, template_id: str) -> dict:
    """Convert a core output port dict to camelCase frontend format."""
    port = {
        "id": p["id"],
        "handleId": p.get("handle_id", "output"),
        "position": p.get("position", "right"),
        "label": p.get("label", p["id"].title()),
    }
    port["labelKey"] = "common.ports.error" if p["id"] == "error" else f"templates.{template_id}.ports.{p['id']}"
    if p.get("event"):
        port["event"] = p["event"]
    if p.get("color"):
        port["color"] = p["color"]
    if p.get("edge_type"):
        port["edgeType"] = p["edge_type"]
    elif p.get("event") == "error":
        port["edgeType"] = "control"
    else:
        port["dataType"] = p.get("data_type", "object")
        port["edgeType"] = "data"
    return port


def _load_core_subflow_ports():
    """Load SUBFLOW port definitions from flyto-core. Returns (input, output) or (None, None)."""
    try:
        from core.modules.types.ports import DEFAULT_PORTS_BY_NODE_TYPE
        from core.modules.types.enums import NodeType
        subflow_ports = DEFAULT_PORTS_BY_NODE_TYPE.get(NodeType.SUBFLOW, {})
        return subflow_ports.get("input", []), subflow_ports.get("output", [])
    except ImportError:
        return None, None


def _get_template_ports(template_id: str):
    """
    Get input/output port definitions for a template module.

    Reads from flyto-core's DEFAULT_PORTS_BY_NODE_TYPE[SUBFLOW] (SSOT) and
    adds template-specific label keys. Falls back to inline defaults if core
    is not importable (cloud-only context).

    Returns:
        (input_ports, output_ports) tuple
    """
    core_input, core_output = _load_core_subflow_ports()

    if core_input is not None and core_output is not None:
        return (
            [_convert_input_port(p, template_id) for p in core_input],
            [_convert_output_port(p, template_id) for p in core_output],
        )

    # Fallback: hardcoded defaults matching SUBFLOW port spec.
    logger.debug("[_get_template_ports] core not available, using inline fallback")
    input_ports = [
        {
            "id": "input", "handleId": "target", "position": "left",
            "label": "Input", "labelKey": f"templates.{template_id}.ports.input",
            "dataType": "any", "edgeType": "data", "maxConnections": 1, "required": True,
        }
    ]
    output_ports = [
        {
            "id": "success", "handleId": "output", "position": "right",
            "label": "Success", "labelKey": f"templates.{template_id}.ports.success",
            "dataType": "object", "edgeType": "data", "event": "success", "color": "#10B981",
        },
        {
            "id": "error", "handleId": "source-error", "position": "right",
            "label": "Error", "labelKey": "common.ports.error",
            "event": "error", "color": "#EF4444", "edgeType": "control",
        }
    ]
    return input_ports, output_ports


def normalize_template(raw: Dict[str, Any], template_id: str, library_id: str = None) -> CanonicalModule:
    """
    Convert user template data to CanonicalModule format.

    Input comes from: catalog.py -> get_workspace_templates_as_modules()

    Args:
        raw: Workflow definition from the local CE workspace
        template_id: Template ID (always the actual template ID)
        library_id: Local workflow ID. Defaults to template_id.

    Returns:
        CanonicalModule with all fields populated
    """
    name = raw.get("name", "Untitled Template")
    description = raw.get("description", "")
    category = raw.get("category", "template")
    icon_url = raw.get("icon_url")
    steps = raw.get("steps", [])
    ui_config = raw.get("ui", {})

    # Create module ID for the template
    module_id = generate_module_id("template", "invoke", template_id)

    # Determine icon and color
    icon_raw = ui_config.get("icon") or "FileText"
    color = ui_config.get("color") or "#8B5CF6"  # Purple for templates

    if steps and len(steps) > 0:
        first_step = steps[0]
        if not ui_config.get("icon") and first_step.get("icon"):
            icon_raw = first_step.get("icon")
        if not ui_config.get("color") and first_step.get("color"):
            color = first_step.get("color")

    # Normalize icon
    if icon_url:
        icon = {"type": "url", "value": icon_url}
    else:
        icon = normalize_icon(icon_raw, color)

    # Build input/output ports from core's SUBFLOW port definition (SSOT).
    # Templates are invoked as subflows; core defines the canonical ports.
    # We add template-specific labelKeys on top.
    input_ports, output_ports = _get_template_ports(template_id)

    # Get params_schema: prefer stored schema, fallback to dynamic computation
    params_schema_raw = get_value_with_aliases(raw, 'params_schema', 'paramsSchema')

    if not params_schema_raw:
        # Backwards compatibility: compute dynamically for old templates
        try:
            from services.template.schema_builder import build_params_schema_for_template
            params_schema_raw = build_params_schema_for_template(raw)
            logger.debug(f"[normalize_template] {template_id} computed paramsSchema (fallback)")
        except ImportError:
            params_schema_raw = {"type": "object", "properties": {}}

    # Normalize params schema
    params_schema = normalize_params_schema(params_schema_raw)

    # If no UI-defined params, extract ${xxx} variables from workflow steps
    visible_props = [k for k, v in params_schema.get("properties", {}).items() if not v.get("hidden")]
    if not visible_props:
        all_variables = extract_variables_from_steps(steps)
        for var_name in sorted(all_variables):
            label = var_name.replace('_', ' ').title()
            params_schema["properties"][var_name] = {
                "type": "string",
                "label": label,
                "description": "",
                "hidden": False,
            }

    params_schema = add_hidden_markers(params_schema)
    default_params = compute_default_params(params_schema)

    # Use pre-computed output_schema (stored at save time), fallback to last step
    output_schema = get_value_with_aliases(raw, 'output_schema', 'outputSchema')
    if not output_schema or not output_schema.get("properties"):
        output_schema = {"type": "object", "properties": {}}
        if steps and len(steps) > 0:
            last_step = steps[-1]
            if last_step.get("outputSchema"):
                output_schema = last_step.get("outputSchema")

    # Extract permissions and capabilities
    extracted = extract_permissions_from_steps(steps)
    permissions = extracted['permissions']
    required_secrets = extracted['required_secrets']
    side_effects = extracted['side_effects']
    provides = extracted['provides']
    consumes = extracted['consumes']

    # Source data for template
    source_data = {
        "templateId": template_id,
        "libraryId": library_id or template_id,
        "steps": steps,
        "stepsCount": len(steps),
        "canStartWorkflow": True,
        "sideEffects": list(side_effects),
        "provides": list(provides),
        "consumes": list(consumes),
        "entrypoint": {
            "type": "template",
            "templateId": template_id,
            "runtime": "flyto-core",
        },
        "ui": {
            "icon": icon,
            "color": color,
            "visibility": "default",
            "group": "My Templates",
            "sections": ui_config.get("sections", []),
            "components": ui_config.get("components", []),
        },
    }

    # Create canonical module using factory function
    result = create_canonical_module(
        module_id=module_id,
        label=name,
        category="my-templates",
        source="template",

        # Display
        description=description,
        icon=icon,
        color=color,
        group="My Templates",
        tier="standard",
        visibility="default",
        tags=[category, "template", "my-templates"],
        labelKey=f"templates.{template_id}.label",
        descriptionKey=f"templates.{template_id}.description",

        # Schema
        paramsSchema=params_schema,
        defaultParams=default_params,
        outputSchema=output_schema,

        # Connection
        inputTypes=["*"],
        outputTypes=["object"],
        canReceiveFrom=["*"],
        canConnectTo=["*"],
        inputPorts=input_ports,
        outputPorts=output_ports,

        # Node
        nodeType="template",

        # AI flags
        isAIModel=False,
        isMemory=False,
        isTool=False,
        isTemplate=True,

        # UI flags
        requiresCustomUI=detect_requires_custom_ui(module_id, raw),

        # Execution
        timeout=60.0 + (len(steps) * 10.0),  # Base 60s + 10s per step
        retryable=True,
        maxRetries=3,
        concurrentSafe=True,
        requiresCredentials=len(required_secrets) > 0,
        requiredPermissions=list(permissions),
        requiredSecrets=list(required_secrets),

        # Metadata
        version=raw.get("version", "1.0.0"),
        stability="stable",
        deprecated=False,

        # Source data
        sourceData=source_data,
    )

    # Enrich with node configuration (uiConfig, handles derived from ports)
    result = enrich_module_with_node_config(result)

    # Add snake_case aliases if enabled for backward compatibility
    if INCLUDE_SNAKE_CASE_ALIASES:
        result = add_snake_case_aliases(result)

    return result
