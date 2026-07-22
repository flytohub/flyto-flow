"""
Template YAML Export/Import Service

Converts between internal template representation and the unified YAML format.
Execution data (steps, params, edges) is the main body; UI data (_ui) is optional.

Split into focused modules:
- yaml_step_parser.py      — step-level parsing, schema conversion, sanitization
- yaml_connection_parser.py — validation (edges, refs, builder bindings)
"""

import re
from typing import Dict, Any, List

import yaml

from .yaml_step_parser import (  # noqa: F401 — re-exported for backward compatibility
    _SENSITIVE_PARAM_PATTERNS,
    _SENSITIVE_RE,
    _UI_STEP_KEYS,
    _sanitize_param_value,
    _sanitize_step_params,
    _args_to_params_schema,
    _params_schema_to_args,
    _normalize_ui_components,
)
from .yaml_connection_parser import (  # noqa: F401 — re-exported for backward compatibility
    validate_template_data,
    _check_step_refs,
    _collect_builder_variables,
    _collect_bracket_vars,
    _BRACKET_VAR_RE,
    _STEP_REF_RE,
)

# --- Custom YAML dumper to prevent type coercion on round-trip ---

class _SafeRoundtripDumper(yaml.SafeDumper):
    """Dumper that quotes ambiguous strings and uses literal blocks for multiline."""
    pass

_YAML_BOOL_STRINGS = frozenset({
    'true', 'false', 'yes', 'no', 'on', 'off',
    'y', 'n', 'null', 'none', '~',
})


def _roundtrip_str_representer(dumper, data):
    """Represent strings with quoting when they'd be misinterpreted by safe_load."""
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    if data.strip().lower() in _YAML_BOOL_STRINGS:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    stripped = data.strip()
    if stripped:
        try:
            float(stripped)
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
        except ValueError:
            pass
    if data == '':
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


_SafeRoundtripDumper.add_representer(str, _roundtrip_str_representer)

# Local database timestamps are not part of the portable workflow definition.
_EXCLUDED_TOP_LEVEL_KEYS = {"created_at", "updated_at"}


_PARAMS_REF_RE = re.compile(r'\$\{params\.(\w+)\}')


def _fix_param_refs(params: Any) -> None:
    """Fix AI-generated '${params.xxx}' → '{{xxx}}' in step params (in-place).

    flyto-core uses {{xxx}} for workflow arg substitution.
    AI sometimes generates ${params.xxx} which is the internal resolved form.
    """
    if not isinstance(params, dict):
        return
    for key, val in params.items():
        if isinstance(val, str) and '${params.' in val:
            params[key] = _PARAMS_REF_RE.sub(r'{{\1}}', val)
        elif isinstance(val, dict):
            _fix_param_refs(val)
        elif isinstance(val, list):
            for i, item in enumerate(val):
                if isinstance(item, str) and '${params.' in item:
                    val[i] = _PARAMS_REF_RE.sub(r'{{\1}}', item)
                elif isinstance(item, dict):
                    _fix_param_refs(item)


def _build_yaml_document(
    template: Dict[str, Any],
    steps: List[Dict],
    include_ui: bool,
    redact_secrets: bool,
) -> Dict[str, Any]:
    """Build the YAML document dict from template data and processed steps."""
    doc: Dict[str, Any] = {}

    # --- Portable execution layer shared with flyto-core ---
    doc["name"] = template.get("name", "Untitled")
    if template.get("description"):
        doc["description"] = template["description"]

    version_tag = template.get("version_tag") or template.get("version")
    if not version_tag:
        vn = template.get("version_number")
        version_tag = f"v{vn}" if vn else "v1"
    doc["version"] = version_tag

    if template.get("category"):
        doc["category"] = template["category"]

    if template.get("tags"):
        doc["tags"] = template["tags"]

    if template.get("required_secrets"):
        doc["required_secrets"] = template["required_secrets"]

    if template.get("dependencies"):
        doc["dependencies"] = template["dependencies"]

    tv = template.get("template_version")
    if tv and tv != "1.0.0":
        doc["template_version"] = tv

    # Args — convert params_schema back to YAML args format
    params_schema = template.get("params_schema")
    if params_schema and isinstance(params_schema, dict):
        args = _params_schema_to_args(params_schema)
        if args:
            doc["args"] = args

    # i18n
    if template.get("default_language") and template["default_language"] != "en":
        doc["default_language"] = template["default_language"]
    if template.get("translations"):
        doc["translations"] = template["translations"]

    # Top-level params (workflow input parameters)
    if template.get("params"):
        doc["params"] = template["params"]

    # Error handling
    if template.get("error_workflow_id"):
        doc["error_workflow_id"] = template["error_workflow_id"]
    if template.get("error_handling"):
        doc["error_handling"] = template["error_handling"]

    # Template-as-Node schemas
    if template.get("input_schema"):
        doc["input_schema"] = template["input_schema"]
    if template.get("output_schema"):
        doc["output_schema"] = template["output_schema"]

    # Steps — strip UI fields out, collect them for _ui block
    positions: Dict[str, list] = {}
    pinned: Dict[str, Any] = {}
    node_state: Dict[str, Any] = {}

    clean_steps: List[Dict] = []
    for step in steps:
        s = dict(step)
        sid = s.get("id", "")

        # Extract position
        px = s.pop("position_x", None)
        py = s.pop("position_y", None)
        if px is not None or py is not None:
            positions[sid] = [px or 0, py or 0]

        # Extract pinned output
        po = s.pop("pinned_output", None)
        if po is not None:
            pinned[sid] = po

        # Extract ui_state
        us = s.pop("ui_state", None)
        if us is not None:
            node_state[sid] = us

        # Sanitize secrets
        if redact_secrets and "params" in s:
            s["params"] = _sanitize_step_params(s["params"])

        clean_steps.append(s)

    doc["steps"] = clean_steps

    # Edges
    if template.get("edges"):
        doc["edges"] = template["edges"]

    # Checkpoints (human-in-the-loop pause points)
    if template.get("checkpoints"):
        doc["checkpoints"] = template["checkpoints"]

    # --- Flyto2 Flow UI layer; flyto-core ignores this metadata ---
    if include_ui:
        _ui: Dict[str, Any] = {}
        if positions:
            _ui["positions"] = positions
        if pinned:
            _ui["pinned"] = pinned
        if node_state:
            _ui["node_state"] = node_state
        if template.get("ui"):
            ui_data = dict(template["ui"])
            # Extract viewport from ui dict into _ui block
            vp = ui_data.pop("viewport", None)
            if vp:
                _ui["viewport"] = vp
            _ui["builder"] = ui_data
        if _ui:
            doc["_ui"] = _ui

    return doc


def export_yaml(template: Dict[str, Any], *, include_ui: bool = True, redact_secrets: bool = True) -> str:
    """Convert internal template dict to unified YAML string.

    Args:
        template: Template dict (from DB / DTO).
        include_ui: Whether to include the _ui block with positions etc.
        redact_secrets: Whether to replace sensitive param values with placeholders.

    Returns:
        YAML string ready for download / file save.
    """
    steps = template.get("steps") or []
    doc = _build_yaml_document(template, steps, include_ui, redact_secrets)
    return yaml.dump(doc, Dumper=_SafeRoundtripDumper, allow_unicode=True,
                     sort_keys=False, default_flow_style=False)


def diff_yaml(
    base: Dict[str, Any],
    proposed: Dict[str, Any],
    *,
    redact_secrets: bool = True,
) -> Dict[str, Any]:
    """Compare two template dicts and return a structured diff.

    Returns a dict with:
    - base_yaml / proposed_yaml: full YAML strings for side-by-side view
    - added_steps, removed_steps, modified_steps, layout_only_steps
    - changed_fields: top-level metadata fields that differ
    """
    base_yaml = export_yaml(base, include_ui=False, redact_secrets=redact_secrets)
    proposed_yaml = export_yaml(proposed, include_ui=False, redact_secrets=redact_secrets)

    # Step-level diff
    base_steps = base.get("steps") or []
    proposed_steps = proposed.get("steps") or []

    base_ids = {s.get("id") for s in base_steps if s.get("id")}
    proposed_ids = {s.get("id") for s in proposed_steps if s.get("id")}

    added = sorted(proposed_ids - base_ids)
    removed = sorted(base_ids - proposed_ids)

    import json
    modified = []
    layout_only = []
    for ps in proposed_steps:
        pid = ps.get("id")
        if pid and pid in base_ids:
            bs = next((s for s in base_steps if s.get("id") == pid), None)
            if not bs:
                continue
            bs_clean = {k: v for k, v in bs.items() if k not in _UI_STEP_KEYS}
            ps_clean = {k: v for k, v in ps.items() if k not in _UI_STEP_KEYS}
            if json.dumps(bs_clean, sort_keys=True) != json.dumps(ps_clean, sort_keys=True):
                modified.append(pid)
            elif json.dumps(bs, sort_keys=True) != json.dumps(ps, sort_keys=True):
                layout_only.append(pid)

    # Metadata diff
    compare_keys = ["name", "description", "tags", "version"]
    changed_fields = [
        k for k in compare_keys
        if base.get(k) != proposed.get(k)
    ]

    return {
        "base_yaml": base_yaml,
        "proposed_yaml": proposed_yaml,
        "added_steps": added,
        "removed_steps": removed,
        "modified_steps": modified,
        "layout_only_steps": layout_only,
        "changed_fields": changed_fields,
        "is_same": base_yaml == proposed_yaml,
    }


def _parse_yaml_document(yaml_str: str) -> Dict[str, Any]:
    """Parse YAML string and validate basic structure."""
    doc = yaml.safe_load(yaml_str)
    if not isinstance(doc, dict):
        raise ValueError("Invalid YAML: root must be a mapping")
    return doc


def _auto_fix_ai_format(steps: List[Dict]) -> None:
    """Fix common AI/flyto-core format mismatches in steps (in-place).

    Handles: type->module, module_id->module, ${params.xxx}->{{xxx}},
    auto-generate missing step IDs.
    """
    for step in steps:
        # Fix 'type' → 'module' (AI often uses 'type' instead of 'module')
        if "module" not in step and "type" in step:
            step["module"] = step.pop("type")
        # Fix 'module_id' or 'moduleId' → 'module'
        if "module" not in step:
            for alt in ("module_id", "moduleId", "node_type"):
                if alt in step:
                    step["module"] = step.pop(alt)
                    break
        # Auto-generate 'id' if missing (use module name + index)
        if "id" not in step:
            idx = steps.index(step)
            module_name = step.get("module", "step")
            # e.g. "browser_launch_0" from "browser.launch"
            step["id"] = f"{module_name.replace('.', '_')}_{idx}"
        # Fix '${params.xxx}' → '{{xxx}}' (AI mixes arg substitution formats)
        _fix_param_refs(step.get("params"))


def _validate_imported_steps(result: Dict[str, Any]) -> None:
    """Validate the imported template structure, raising ValueError on failure."""
    errors = validate_template_data(result)
    if errors:
        raise ValueError(
            "YAML validation failed: " + "; ".join(errors[:10])
        )


def import_yaml(yaml_str: str) -> Dict[str, Any]:
    """Parse a unified YAML string into a template data dict.

    The returned dict can be passed directly to template create/update APIs.

    Returns:
        Dict with keys: name, description, tags, steps, edges, ui,
        needs_auto_layout (bool).
    """
    doc = _parse_yaml_document(yaml_str)

    steps: List[Dict] = doc.get("steps") or []
    _ui: Dict[str, Any] = doc.get("_ui") or {}

    _auto_fix_ai_format(steps)

    # Restore positions from _ui into steps
    positions = _ui.get("positions") or {}
    for step in steps:
        sid = step.get("id")
        if sid and sid in positions:
            pos = positions[sid]
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                step["position_x"] = pos[0]
                step["position_y"] = pos[1]

    # Restore pinned output
    pinned = _ui.get("pinned") or {}
    for step in steps:
        sid = step.get("id")
        if sid and sid in pinned:
            step["pinned_output"] = pinned[sid]

    # Restore node_state
    node_state = _ui.get("node_state") or {}
    for step in steps:
        sid = step.get("id")
        if sid and sid in node_state:
            step["ui_state"] = node_state[sid]

    has_positions = bool(positions) or any(
        "position_x" in s or "position_y" in s for s in steps
    )

    result: Dict[str, Any] = {
        "name": doc.get("name") or "Imported Template",
        "description": doc.get("description") or "",
        "category": doc.get("category") or "other",
        "tags": doc.get("tags") or [],
        "steps": steps,
        "needs_auto_layout": not has_positions,
    }

    if doc.get("edges"):
        result["edges"] = doc["edges"]

    if doc.get("params"):
        result["params"] = doc["params"]

    if doc.get("required_secrets"):
        result["required_secrets"] = doc["required_secrets"]

    if doc.get("dependencies"):
        result["dependencies"] = doc["dependencies"]
    if doc.get("template_version"):
        result["template_version"] = doc["template_version"]

    # i18n
    if doc.get("translations"):
        result["translations"] = doc["translations"]
    if doc.get("default_language"):
        result["default_language"] = doc["default_language"]

    # Version
    if doc.get("version"):
        result["version_tag"] = doc["version"]

    # Error handling
    if doc.get("error_workflow_id"):
        result["error_workflow_id"] = doc["error_workflow_id"]
    if doc.get("error_handling"):
        result["error_handling"] = doc["error_handling"]

    # Template-as-Node schemas
    if doc.get("input_schema"):
        result["input_schema"] = doc["input_schema"]
    if doc.get("output_schema"):
        result["output_schema"] = doc["output_schema"]

    # Checkpoints (human-in-the-loop pause points)
    if doc.get("checkpoints"):
        result["checkpoints"] = doc["checkpoints"]

    builder = _ui.get("builder")
    if builder:
        _normalize_ui_components(builder)
        result["ui"] = builder

    # Convert YAML args to params_schema (JSON Schema format)
    # Always generate when args is present — builder defines UI layout,
    # params_schema defines the JSON Schema; both can coexist.
    args_def = doc.get("args")
    if args_def and isinstance(args_def, dict):
        result["params_schema"] = _args_to_params_schema(args_def)
    # Restore viewport into ui dict
    vp = _ui.get("viewport")
    if vp:
        if "ui" not in result or result["ui"] is None:
            result["ui"] = {}
        result["ui"]["viewport"] = vp

    # Generate edges from step connections/order if no explicit edges
    if not result.get("edges") and steps:
        try:
            from services.helpers.workflow_helpers import generate_edges_from_steps
            generated = generate_edges_from_steps(steps)
            if generated:
                result["edges"] = generated
        except ImportError:
            pass

    _validate_imported_steps(result)

    return result
