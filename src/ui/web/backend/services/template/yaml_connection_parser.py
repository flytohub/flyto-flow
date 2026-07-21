"""
Validation logic for template YAML — edges, step references, builder bindings.
"""

import re
from typing import Any, Dict, List

from .yaml_step_parser import _UI_STEP_KEYS

_BRACKET_VAR_RE = re.compile(r'\[\[(\w+)\]\]')
_STEP_REF_RE = re.compile(r'\$\{(\w+)\.data(?:\.\w+)*\}')


def validate_template_data(data: Dict[str, Any]) -> List[str]:
    """Validate imported template data and return list of error strings.

    Checks:
    1. Every step has 'id' and 'module'
    2. Edges reference existing step IDs
    3. ${step_id.data...} references point to existing step IDs
    4. [[var]] references in step params have matching builder components
    5. Builder components have 'id' and 'params.variableName'
    """
    errors: List[str] = []
    steps = data.get("steps") or []
    step_ids = set()

    # 1. Validate steps
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"steps[{i}] must be a mapping")
            continue
        sid = step.get("id")
        if not sid:
            errors.append(f"steps[{i}] missing 'id'")
        else:
            step_ids.add(sid)
        if not step.get("module"):
            label = sid or f"steps[{i}]"
            errors.append(f"step '{label}' missing 'module'")

    # 2. Validate edges
    edges = data.get("edges") or []
    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            continue
        src = edge.get("source")
        tgt = edge.get("target")
        if src and src not in step_ids:
            errors.append(f"edge '{edge.get('id', i)}' source '{src}' not found in steps")
        if tgt and tgt not in step_ids:
            errors.append(f"edge '{edge.get('id', i)}' target '{tgt}' not found in steps")

    # 3. Validate ${step_id.data...} references in step params
    for step in steps:
        sid = step.get("id", "?")
        _check_step_refs(step.get("params"), sid, step_ids, errors)

    # 4 & 5. Validate builder components and [[var]] bindings
    builder = data.get("ui")
    builder_vars = set()
    if builder and isinstance(builder, dict):
        builder_vars = _collect_builder_variables(builder, errors)

    # Check [[var]] refs in step params against builder variables
    if builder_vars is not None:
        all_bracket_vars = set()
        for step in steps:
            _collect_bracket_vars(step.get("params"), all_bracket_vars)
        # Also check from args/params_schema
        ps = data.get("params_schema")
        if ps and isinstance(ps, dict):
            for prop_name in ps.get("properties", {}):
                all_bracket_vars.discard(prop_name)
        unbound = all_bracket_vars - builder_vars
        # Only warn for vars that have no builder AND no params_schema binding
        if unbound and builder:
            for var in sorted(unbound):
                errors.append(
                    f"[[{var}]] used in step params but no matching builder component "
                    f"or args definition found"
                )

    return errors


def _check_step_refs(
    value: Any, step_id: str, valid_ids: set, errors: List[str]
) -> None:
    """Recursively check ${step.data...} references in param values."""
    if isinstance(value, str):
        for m in _STEP_REF_RE.finditer(value):
            ref_id = m.group(1)
            if ref_id not in valid_ids:
                errors.append(
                    f"step '{step_id}' references '${{{ref_id}.data...}}' "
                    f"but step '{ref_id}' does not exist"
                )
    elif isinstance(value, dict):
        for v in value.values():
            _check_step_refs(v, step_id, valid_ids, errors)
    elif isinstance(value, list):
        for v in value:
            _check_step_refs(v, step_id, valid_ids, errors)


def _collect_builder_variables(
    builder: Dict[str, Any], errors: List[str]
) -> set:
    """Collect all variableName values from builder components.

    Also validates that components have 'id' and 'params.variableName'.
    """
    var_names = set()
    sections = builder.get("sections")
    if not sections or not isinstance(sections, list):
        return var_names

    for i, sec in enumerate(sections):
        if not isinstance(sec, dict):
            continue
        for col in (sec.get("columnsData") or []):
            if not isinstance(col, dict):
                continue
            for k, comp in enumerate(col.get("components") or []):
                if not isinstance(comp, dict):
                    continue
                comp_id = comp.get("id")
                if not comp_id:
                    errors.append(
                        f"sections[{i}] component[{k}] missing 'id'"
                    )
                params = comp.get("params")
                vname = None
                if isinstance(params, dict):
                    vname = params.get("variableName") or params.get("variable_name")
                if vname:
                    var_names.add(vname)
                elif comp.get("type") == "input":
                    label = comp_id or f"component[{k}]"
                    errors.append(
                        f"builder component '{label}' missing 'params.variableName'"
                    )
    return var_names


def _collect_bracket_vars(value: Any, result: set) -> None:
    """Recursively collect all [[var]] variable names from a value."""
    if isinstance(value, str):
        for m in _BRACKET_VAR_RE.finditer(value):
            result.add(m.group(1))
    elif isinstance(value, dict):
        for v in value.values():
            _collect_bracket_vars(v, result)
    elif isinstance(value, list):
        for v in value:
            _collect_bracket_vars(v, result)
