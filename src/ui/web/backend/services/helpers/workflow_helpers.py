"""
Workflow Helpers

Helper functions for workflow transformations.
Centralizes logic for generating edges from steps for backward compatibility.
"""

from typing import Dict, List, Any, Optional


def _iter_resource_node_ids(resource_value: Any) -> List[str]:
    """Return resource node IDs from a scalar or list-valued resource ref."""
    if isinstance(resource_value, list):
        return [item for item in resource_value if isinstance(item, str) and item]
    if isinstance(resource_value, str) and resource_value:
        return [resource_value]
    return []


def build_step_node_data(
    step: Dict[str, Any],
    module_id: str,
    label: str,
    params: Any,
    connections: Any,
) -> Dict[str, Any]:
    """Build the VueFlow node data dict from a workflow step."""
    data = {
        "module": module_id,
        "label": label,
        "params": params,
        "connections": connections,
        "description": step.get("description"),
        "output": step.get("output"),
        "when": step.get("when"),
        "on_error": step.get("on_error"),
        "retry": step.get("retry"),
        "timeout": step.get("timeout"),
        "parallel": step.get("parallel"),
        "foreach": step.get("foreach"),
        "as": step.get("as"),
    }

    # Detect sub-node type from module ID pattern.
    # Works on both Cloud API (no flyto-core) and Worker (has flyto-core).
    _AI_SUB_PREFIXES = ("ai.model", "ai.memory", "ai.memory_", "ai.tool", "ai.embed", "ai.vision")
    if module_id and any(module_id.startswith(p) for p in _AI_SUB_PREFIXES):
        data["isSubNode"] = True
        sub_type = module_id.split(".")[-1] if "." in module_id else module_id
        # Normalize to standard types
        if "model" in sub_type or sub_type in ("embed", "vision_analyze"):
            data["subNodeType"] = "model"
        elif "memory" in sub_type:
            data["subNodeType"] = "memory"
        else:
            data["subNodeType"] = "tool"

    # Also check step-level hint (from YAML resources field)
    if step.get("is_sub_node") or step.get("isSubNode"):
        data["isSubNode"] = True
        if not data.get("subNodeType"):
            data["subNodeType"] = step.get("sub_node_type") or step.get("subNodeType") or "tool"

    return data


def _build_step_maps(
    steps: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build lookup maps from steps for edge generation.

    Returns a dict with:
        step_id_map: step ID -> index
        step_module_map: step ID -> module ID
        resource_node_ids: set of resource sub-node IDs
        explicit_connection_nodes: set of flow-control node IDs with connections
        loop_body_node_ids: set of loop body start node IDs
    """
    from services.graph_helpers import (
        is_loop_module,
        is_branch_module,
        is_switch_module,
    )

    step_id_map = {step.get("id"): idx for idx, step in enumerate(steps)}
    step_module_map = {step.get("id"): (step.get("module") or step.get("type") or "") for step in steps}

    # Identify resource nodes (AI Agent sub-nodes) - they don't participate in sequential flow
    resource_node_ids = set()
    for step in steps:
        if step.get("resources"):
            for res_type, res_node_id in step["resources"].items():
                for node_id in _iter_resource_node_ids(res_node_id):
                    resource_node_ids.add(node_id)

    # Track nodes with explicit connections and loop body nodes
    explicit_connection_nodes = set()
    loop_body_node_ids = set()
    for step in steps:
        step_id = step.get("id")
        module_id = step.get("module", "")
        connections = step.get("connections") or {}
        if step_id and connections and (is_loop_module(module_id) or is_branch_module(module_id) or is_switch_module(module_id)):
            explicit_connection_nodes.add(step_id)
        # Collect loop body nodes (iterate targets) — they get edges from the loop node, not sequential
        if is_loop_module(module_id):
            iterate_raw = connections.get("iterate")
            if iterate_raw:
                targets = iterate_raw if isinstance(iterate_raw, list) else [iterate_raw]
                loop_body_node_ids.update(targets)
            elif (step.get("params") or {}).get("target"):
                loop_body_node_ids.add(step["params"]["target"])

    return {
        "step_id_map": step_id_map,
        "step_module_map": step_module_map,
        "resource_node_ids": resource_node_ids,
        "explicit_connection_nodes": explicit_connection_nodes,
        "loop_body_node_ids": loop_body_node_ids,
    }


def _generate_sequential_edges(
    main_flow_node_ids: List[str],
    maps: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate sequential flow edges between main-flow nodes."""
    from services.graph_helpers import get_target_handle

    edges = []
    explicit_connection_nodes = maps["explicit_connection_nodes"]
    loop_body_node_ids = maps["loop_body_node_ids"]
    step_module_map = maps["step_module_map"]

    for i in range(len(main_flow_node_ids) - 1):
        source_id = main_flow_node_ids[i]
        target_id = main_flow_node_ids[i + 1]

        # Skip: flow control nodes with explicit connections, and loop body nodes
        if source_id in explicit_connection_nodes or source_id in loop_body_node_ids:
            continue

        target_module = step_module_map.get(target_id, "")
        edges.append({
            "id": f"e_{source_id}_{target_id}",
            "source": source_id,
            "target": target_id,
            "sourceHandle": "output",  # Match VueFlow handle ID in DefaultNode.vue
            "targetHandle": get_target_handle(target_module),  # 'in' for LoopNode, 'target' for others
            "type": "straight",
            "data": {"edgeType": "sequential"}
        })

    return edges


def _generate_loop_edges(
    steps: List[Dict[str, Any]],
    maps: Dict[str, Any],
    include_labels: bool,
) -> List[Dict[str, Any]]:
    """Generate loop iterate and done edges."""
    from services.graph_helpers import is_loop_module, get_target_handle

    edges = []
    step_id_map = maps["step_id_map"]
    step_module_map = maps["step_module_map"]

    for step in steps:
        module_id = step.get("module", "")
        if not is_loop_module(module_id):
            continue

        step_id = step.get("id")
        connections = step.get("connections") or {}
        params = step.get("params") or {}

        # Get iterate target from connections or params.target (for backward compatibility)
        # connections values can be string ("nodeId") or list (["nodeId"])
        iterate_target = None
        if connections.get("iterate"):
            targets = connections["iterate"]
            iterate_target = targets[0] if isinstance(targets, list) and targets else targets
        elif params.get("target"):
            iterate_target = params.get("target")

        done_target = None
        if connections.get("done"):
            targets = connections["done"]
            done_target = targets[0] if isinstance(targets, list) and targets else targets

        # Create edge from loop node to loop body (iterate/body_out -> target-top)
        if iterate_target and iterate_target in step_id_map:
            iterate_edge = {
                "id": f"loop_iterate_{step_id}_{iterate_target}",
                "source": step_id,
                "target": iterate_target,
                "sourceHandle": "body_out",
                "targetHandle": "target-top",
                "type": "smoothstep",
                "data": {"edgeType": "iterate"}
            }
            if include_labels:
                iterate_edge["label"] = "Iterate"
            edges.append(iterate_edge)
            # Note: No loop-back edge rendered — ForEach node UI already implies looping.
            # The iterate edge (loop->body) + done edge (loop->next) are sufficient.

        if done_target and done_target in step_id_map:
            target_module = step_module_map.get(done_target, "")
            done_edge = {
                "id": f"loop_done_{step_id}_{done_target}",
                "source": step_id,
                "target": done_target,
                "sourceHandle": "done_out",
                "targetHandle": get_target_handle(target_module),
                "type": "smoothstep",
                "data": {"edgeType": "done"}
            }
            if include_labels:
                done_edge["label"] = "Done"
            edges.append(done_edge)

    return edges


def _generate_branch_edges(
    steps: List[Dict[str, Any]],
    maps: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate branch true/false edges."""
    from services.graph_helpers import is_branch_module, get_target_handle

    edges = []
    step_id_map = maps["step_id_map"]
    step_module_map = maps["step_module_map"]

    for step in steps:
        module_id = step.get("module", "")
        if not is_branch_module(module_id):
            continue

        step_id = step.get("id")
        connections = step.get("connections") or {}

        true_target = connections.get("true")
        true_target = true_target[0] if isinstance(true_target, list) else true_target

        false_target = connections.get("false")
        false_target = false_target[0] if isinstance(false_target, list) else false_target

        if true_target and true_target in step_id_map:
            target_module = step_module_map.get(true_target, "")
            edges.append({
                "id": f"branch_true_{step_id}_{true_target}",
                "source": step_id,
                "target": true_target,
                "sourceHandle": "source-true",
                "targetHandle": get_target_handle(target_module),
                "type": "smoothstep",
                "data": {"edgeType": "control"}
            })

        if false_target and false_target in step_id_map:
            target_module = step_module_map.get(false_target, "")
            edges.append({
                "id": f"branch_false_{step_id}_{false_target}",
                "source": step_id,
                "target": false_target,
                "sourceHandle": "source-false",
                "targetHandle": get_target_handle(target_module),
                "type": "smoothstep",
                "data": {"edgeType": "control"}
            })

    return edges


def _generate_switch_edges(
    steps: List[Dict[str, Any]],
    maps: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate switch case edges."""
    from services.graph_helpers import is_switch_module, get_target_handle

    edges = []
    step_id_map = maps["step_id_map"]
    step_module_map = maps["step_module_map"]

    for step in steps:
        module_id = step.get("module", "")
        if not is_switch_module(module_id):
            continue

        step_id = step.get("id")
        connections = step.get("connections") or {}
        params = step.get("params") or {}

        for key, value in connections.items():
            if not value:
                continue
            target_id = value[0] if isinstance(value, list) else value
            if not target_id or target_id not in step_id_map:
                continue

            if key == "default":
                source_handle = "source-default"
            else:
                source_handle = resolve_switch_case_handle(key, params)
                if not source_handle:
                    continue

            target_module = step_module_map.get(target_id, "")
            edges.append({
                "id": f"switch_{step_id}_{key}_{target_id}",
                "source": step_id,
                "target": target_id,
                "sourceHandle": source_handle,
                "targetHandle": get_target_handle(target_module),
                "type": "smoothstep",
                "data": {"edgeType": "control"}
            })

    return edges


def _generate_resource_edges(
    steps: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate resource attachment edges for AI Agent sub-nodes."""
    edges = []

    for step in steps:
        if not step.get("resources"):
            continue

        agent_node_id = step["id"]
        for res_type, res_node_id in step["resources"].items():
            for node_id in _iter_resource_node_ids(res_node_id):
                edges.append({
                    "id": f"res_{node_id}_{agent_node_id}_{res_type}",
                    "source": node_id,
                    "target": agent_node_id,
                    "sourceHandle": "target",  # AISubNode.vue handle id
                    "targetHandle": f"target-{res_type}",
                    "type": "smoothstep",
                    "data": {"edgeType": "resource"}
                })

    return edges


def generate_edges_from_steps(
    steps: List[Dict[str, Any]],
    *,
    include_labels: bool = False,
    main_flow_node_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate edges from step connections for backward compatibility.

    This is used when loading templates that only have steps with connections
    but no edges array. It generates the edges that the frontend needs.
    Also used by convert_steps_to_vueflow() to avoid duplicating edge-building logic.

    Args:
        steps: List of workflow steps
        include_labels: If True, add human-readable labels to loop edges
            (e.g. "Iterate", "Done"). Used by VueFlow rendering.
        main_flow_node_ids: Pre-computed ordered list of main-flow node IDs
            (excluding resource nodes). If None, computed from steps.

    Returns:
        List of edge objects for VueFlow
    """
    if not steps:
        return []

    maps = _build_step_maps(steps)

    # Get main flow node IDs (excluding resource nodes)
    if main_flow_node_ids is None:
        main_flow_node_ids = [s.get("id") for s in steps if s.get("id") not in maps["resource_node_ids"]]

    edges = []
    edges.extend(_generate_sequential_edges(main_flow_node_ids, maps))
    edges.extend(_generate_loop_edges(steps, maps, include_labels))
    edges.extend(_generate_branch_edges(steps, maps))
    edges.extend(_generate_switch_edges(steps, maps))
    edges.extend(_generate_resource_edges(steps))

    return edges


def resolve_switch_case_handle(case_key: str, params: dict) -> str:
    """Resolve switch case handle ID from case key."""
    if not case_key or not case_key.startswith("case:"):
        return ""

    case_value = case_key.replace("case:", "")
    cases = params.get("cases") if isinstance(params, dict) else None

    if isinstance(cases, list):
        for item in cases:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id")) if item.get("id") is not None else None
            item_value = str(item.get("value")) if item.get("value") is not None else None
            if item_id == case_value:
                return f"source-case-{item_id}"
            if item_value == case_value:
                return f"source-case-{item_value}"

    return f"source-case-{case_value}"


def ensure_edges_on_template(template_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure template has edges array for frontend compatibility.

    If template only has steps with connections but no edges,
    generate edges from the connections.

    Args:
        template_dict: Template data dictionary

    Returns:
        Template dict with edges array added if missing
    """
    if not template_dict:
        return template_dict

    steps = template_dict.get("steps", [])
    edges = template_dict.get("edges")

    # If no steps, nothing to do
    if not steps:
        return template_dict

    # If already has edges, keep them
    if edges and isinstance(edges, list) and len(edges) > 0:
        return template_dict

    # Generate edges from step connections
    generated_edges = generate_edges_from_steps(steps)

    if generated_edges:
        template_dict["edges"] = generated_edges

    return template_dict


def strip_connections_from_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove connections from steps when edges are the source of truth.

    This is used when saving templates to avoid data duplication.
    The connections can be regenerated from edges when needed.

    Args:
        steps: List of workflow steps

    Returns:
        Steps with connections removed
    """
    if not steps:
        return steps

    result = []
    for step in steps:
        step_copy = dict(step)
        # Remove connections - edges are source of truth
        step_copy.pop("connections", None)
        result.append(step_copy)

    return result
