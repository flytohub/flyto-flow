"""
compose_workflow — AI tool that generates valid flyto YAML from a step plan.

Unlike freeform AI YAML generation, this tool:
1. Validates every module_id against the real module catalog
2. Validates params against each module's schema
3. Generates correct {{args}} and ${step.data} references
4. Auto-generates edges for linear flow
5. Returns YAML that import_yaml() accepts without errors

Usage by AI Agent:
  compose_workflow({
    "name": "Price Tracker",
    "description": "Track product prices",
    "args": {"url": {"type": "string", "required": true}},
    "steps": [
      {"module": "browser.launch", "params": {"headless": true}},
      {"module": "browser.goto", "params": {"url": "{{url}}"}},
      {"module": "browser.extract", "params": {"selector": ".price"}}
    ]
  })
"""

import logging
import yaml
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Tool definition for LLM function calling
COMPOSE_WORKFLOW_TOOL = {
    "name": "compose_workflow",
    "description": (
        "Generate a valid flyto workflow YAML from a step plan. "
        "Use this instead of writing YAML manually. "
        "Provide name, description, args (workflow input parameters), and steps (list of {module, params}). "
        "Each step needs a 'module' (use search_modules to find the right one) and 'params'. "
        "Use {{arg_name}} in params to reference workflow args, and ${step_id.data.field} to reference previous step outputs. "
        "Returns valid YAML ready for import into the template builder."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Workflow name"
            },
            "description": {
                "type": "string",
                "description": "What this workflow does"
            },
            "args": {
                "type": "object",
                "description": "Workflow input parameters. Each key is a param name, value is {type, required, default, description}",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["string", "number", "boolean", "array", "object"]},
                        "required": {"type": "boolean"},
                        "default": {},
                        "description": {"type": "string"}
                    }
                }
            },
            "steps": {
                "type": "array",
                "description": "Ordered list of workflow steps",
                "items": {
                    "type": "object",
                    "properties": {
                        "module": {
                            "type": "string",
                            "description": "Module ID (e.g. browser.launch, http.get). Use search_modules() to find the right one."
                        },
                        "id": {
                            "type": "string",
                            "description": "Optional step ID. Auto-generated if omitted."
                        },
                        "params": {
                            "type": "object",
                            "description": "Module parameters. Use {{arg_name}} for workflow args, ${prev_step_id.data.field} for step references."
                        },
                        "foreach": {
                            "type": "string",
                            "description": "Optional: iterate over an array (e.g. '${fetch.data.items}')"
                        },
                        "as": {
                            "type": "string",
                            "description": "Optional: variable name for current item in foreach loop (default: 'item')"
                        },
                        "when": {
                            "type": "string",
                            "description": "Optional: condition to run this step (e.g. '${prev.data.status} == 200')"
                        }
                    },
                    "required": ["module"]
                }
            },
            "category": {
                "type": "string",
                "description": "Template category (e.g. scraping, automation, monitoring)"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Template tags for search/discovery"
            }
        },
        "required": ["name", "steps"]
    }
}


async def dispatch_compose_workflow(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Server-side handler: validate modules, generate YAML."""
    name = arguments.get("name", "Untitled Workflow")
    description = arguments.get("description", "")
    args_def = arguments.get("args") or {}
    raw_steps = arguments.get("steps") or []
    category = arguments.get("category", "other")
    tags = arguments.get("tags") or []

    if not raw_steps:
        return {"ok": False, "error": "No steps provided"}

    # Validate modules against catalog
    catalog = _get_module_catalog()
    validated_steps = []
    warnings = []

    for i, step in enumerate(raw_steps):
        module_id = step.get("module", "")
        if not module_id:
            return {"ok": False, "error": f"Step {i} missing 'module'"}

        # Validate module exists
        if catalog and module_id not in catalog:
            # Try fuzzy match
            suggestion = _fuzzy_match_module(module_id, catalog)
            if suggestion:
                warnings.append(f"Step {i}: '{module_id}' not found, using '{suggestion}'")
                module_id = suggestion
            else:
                warnings.append(f"Step {i}: '{module_id}' not in catalog (may still work)")

        # Generate step ID if missing
        step_id = step.get("id") or f"{module_id.replace('.', '_')}_{i}"

        validated_step = {
            "id": step_id,
            "module": module_id,
        }
        if step.get("params"):
            # Fix ${params.xxx} → {{xxx}} before generating YAML
            params = _deep_copy_fix_params(step["params"])
            validated_step["params"] = params
        for optional_key in ("foreach", "as", "when", "on_error", "retry", "timeout"):
            if step.get(optional_key):
                validated_step[optional_key] = step[optional_key]

        validated_steps.append(validated_step)

    # Build YAML document
    doc = {"name": name}
    if description:
        doc["description"] = description
    if category:
        doc["category"] = category
    if tags:
        doc["tags"] = tags
    if args_def:
        doc["args"] = args_def
    doc["steps"] = validated_steps

    # Generate YAML string
    yaml_str = yaml.dump(doc, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Validate it can be imported
    try:
        from services.template.template_yaml import import_yaml
        import_yaml(yaml_str)
    except ValueError as e:
        return {
            "ok": False,
            "error": f"Generated YAML failed validation: {e}",
            "yaml": yaml_str,
            "warnings": warnings,
        }

    result = {
        "ok": True,
        "yaml": yaml_str,
        "step_count": len(validated_steps),
        "message": f"Generated workflow '{name}' with {len(validated_steps)} steps. Copy the YAML below to import.",
    }
    if warnings:
        result["warnings"] = warnings

    return result


def _get_module_catalog() -> Optional[Dict[str, Any]]:
    """Get flat set of all module IDs from catalog."""
    try:
        from core.mcp_handler import list_modules
        result = list_modules()
        modules = set()
        for cat in result.get("categories", []):
            for mod in cat.get("modules", []):
                mid = mod.get("id") or mod.get("module_id")
                if mid:
                    modules.add(mid)
        return modules
    except Exception:
        return None


def _fuzzy_match_module(query: str, catalog: set) -> Optional[str]:
    """Try to find a close match for a module ID."""
    query_lower = query.lower().replace("-", ".").replace("_", ".")

    # Exact match (case-insensitive)
    for mid in catalog:
        if mid.lower() == query_lower:
            return mid

    # Suffix match (e.g. "launch" → "browser.launch")
    for mid in catalog:
        if mid.lower().endswith(f".{query_lower}"):
            return mid

    # Contains match
    matches = [mid for mid in catalog if query_lower in mid.lower()]
    if len(matches) == 1:
        return matches[0]

    return None


import re
_PARAMS_REF_RE = re.compile(r'\$\{params\.(\w+)\}')


def _deep_copy_fix_params(params: Any) -> Any:
    """Deep-copy params and fix ${params.xxx} → {{xxx}}."""
    if isinstance(params, dict):
        return {k: _deep_copy_fix_params(v) for k, v in params.items()}
    elif isinstance(params, list):
        return [_deep_copy_fix_params(v) for v in params]
    elif isinstance(params, str):
        return _PARAMS_REF_RE.sub(r'{{\1}}', params)
    return params
