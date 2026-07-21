"""
Steps to VueFlow Converter

Converts backend workflow steps to VueFlow-compatible nodes/edges format
for frontend canvas rendering.
"""

import logging
from copy import deepcopy
from typing import Dict, List, Any, Tuple

from services.graph_helpers import (
    is_loop_module,
    is_branch_module,
)
from services.helpers.workflow_helpers import (
    build_step_node_data,
    generate_edges_from_steps,
)
from services.template.converter_utils import (
    INITIAL_X,
    INITIAL_Y,
    HORIZONTAL_SPACING,
    RESOURCE_SPACING,
    RESOURCE_Y_OFFSET,
)

logger = logging.getLogger(__name__)


def _iter_resource_node_ids(resource_value: Any) -> List[str]:
    """Return resource node IDs from a scalar or list-valued resource ref."""
    if isinstance(resource_value, list):
        return [item for item in resource_value if isinstance(item, str) and item]
    if isinstance(resource_value, str) and resource_value:
        return [resource_value]
    return []


def convert_steps_to_vueflow(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convert backend steps to VueFlow-compatible format.

    Args:
        steps: List of step objects from backend

    Returns:
        {"nodes": [...], "edges": [...]}
    """
    if not steps:
        return {"nodes": [], "edges": []}

    # Phase 1: Auto-detect missing iterate connections on a working copy.
    # Rendering a workflow must not mutate persisted backend step data.
    steps = deepcopy(steps)
    _auto_detect_iterate_connections(steps)

    # Phase 2: Sort steps for consistent layout
    steps, resource_node_ids, resource_to_parent = _sort_steps_for_layout(steps)

    # Phase 3: Create nodes
    step_id_map = {step.get("id"): idx for idx, step in enumerate(steps)}
    main_flow_steps = [s for s in steps if s.get("id") not in resource_node_ids]

    # Collect iterate/done targets from loop nodes for positioning
    iterate_target_to_loop: Dict[str, str] = {}
    done_target_to_loop: Dict[str, str] = {}
    for s in steps:
        mod = s.get("module", s.get("type", ""))
        if is_loop_module(mod) and s.get("connections"):
            iter_raw = s["connections"].get("iterate")
            if iter_raw:
                targets = iter_raw if isinstance(iter_raw, list) else [iter_raw]
                for t in targets:
                    iterate_target_to_loop[t] = s["id"]
            done_raw = s["connections"].get("done")
            if done_raw:
                targets = done_raw if isinstance(done_raw, list) else [done_raw]
                for t in targets:
                    done_target_to_loop[t] = s["id"]

    nodes = []
    for index, step in enumerate(steps):
        node = _create_node(
            step, index, main_flow_steps,
            resource_node_ids, iterate_target_to_loop, done_target_to_loop,
            step_id_map,
        )
        nodes.append(node)

    # Phase 4: Reposition resource nodes below their parent
    _reposition_resource_nodes(nodes, resource_to_parent)

    # Phase 5: Generate edges
    main_flow_node_ids = [n["id"] for n in nodes if n["id"] not in resource_node_ids]
    edges = generate_edges_from_steps(
        steps,
        include_labels=True,
        main_flow_node_ids=main_flow_node_ids,
    )

    return {"nodes": nodes, "edges": edges}


def _auto_detect_iterate_connections(steps: List[Dict[str, Any]]) -> None:
    """Detect and fill missing iterate connections for loop nodes.

    For each loop step that has no iterate target, scan other steps'
    params for ``${step_id.item}`` or ``${loop.item}`` references and
    wire them up automatically.  Mutates *steps* in-place.
    """
    for step in steps:
        module_id = step.get("module", "")
        if not is_loop_module(module_id):
            continue
        connections = step.get("connections") or {}
        if connections.get("iterate"):
            continue  # Already has iterate
        step_id = step.get("id")
        for other in steps:
            if other.get("id") == step_id:
                continue
            params_str = str(other.get("params") or {})
            if f"${{{step_id}.item}}" in params_str or "${loop.item}" in params_str:
                if not step.get("connections"):
                    step["connections"] = {}
                step["connections"]["iterate"] = [other["id"]]
                break


def _sort_steps_for_layout(
    steps: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], set, Dict[str, Dict[str, str]]]:
    """Sort steps for consistent layout and identify resource nodes.

    Returns:
        (ordered_steps, resource_node_ids, resource_to_parent)

    Order: start -> main flow (loop bodies inline after their loop)
    -> end -> remaining (resource nodes etc.)
    """
    step_map = {s.get("id"): s for s in steps}

    # Identify loop body targets
    _body_ids: set = set()
    _loop_bodies: Dict[str, list] = {}
    for s in steps:
        mod = s.get("module", "")
        if is_loop_module(mod):
            conns = s.get("connections") or {}
            iterate_raw = conns.get("iterate")
            if iterate_raw:
                targets = iterate_raw if isinstance(iterate_raw, list) else [iterate_raw]
                _loop_bodies[s["id"]] = targets
                _body_ids.update(targets)
            elif s.get("params", {}).get("target"):
                t = s["params"]["target"]
                _loop_bodies[s["id"]] = [t]
                _body_ids.add(t)

    # Identify resource nodes (AI Agent sub-nodes)
    resource_node_ids: set = set()
    resource_to_parent: Dict[str, Dict[str, str]] = {}
    for step in steps:
        if step.get("resources"):
            for res_type, res_node_id in step["resources"].items():
                for node_id in _iter_resource_node_ids(res_node_id):
                    resource_node_ids.add(node_id)
                    resource_to_parent[node_id] = {
                        "parentId": step["id"],
                        "type": res_type,
                    }

    _start_ids = {s["id"] for s in steps if (s.get("module") or s.get("type")) == "flow.start"}
    _end_ids = {s["id"] for s in steps if (s.get("module") or s.get("type")) == "flow.end"}

    _ordered_ids: List[str] = []
    # Start first
    for s in steps:
        if s["id"] in _start_ids:
            _ordered_ids.append(s["id"])
    # Middle: non-start, non-end, non-body, non-resource
    for s in steps:
        sid = s["id"]
        if sid in _start_ids or sid in _end_ids or sid in _body_ids or sid in resource_node_ids:
            continue
        _ordered_ids.append(sid)
        # Insert loop body nodes right after their loop node
        if sid in _loop_bodies:
            for body_id in _loop_bodies[sid]:
                if body_id not in _ordered_ids:
                    _ordered_ids.append(body_id)
    # End last
    for s in steps:
        if s["id"] in _end_ids:
            _ordered_ids.append(s["id"])
    # Any remaining (resource nodes etc.)
    for s in steps:
        if s["id"] not in _ordered_ids:
            _ordered_ids.append(s["id"])

    ordered_steps = [step_map[sid] for sid in _ordered_ids if sid in step_map]
    return ordered_steps, resource_node_ids, resource_to_parent


def _create_node(
    step: Dict[str, Any],
    index: int,
    main_flow_steps: List[Dict[str, Any]],
    resource_node_ids: set,
    iterate_target_to_loop: Dict[str, str],
    done_target_to_loop: Dict[str, str],
    step_id_map: Dict[str, int],
) -> Dict[str, Any]:
    """Create a single VueFlow node from a step definition.

    Handles position calculation (saved or auto-layout), param
    normalization, and connection initialization for flow control nodes.
    """
    step_id = step.get("id", f"node-{index + 1}")
    module_id = step.get("module", step.get("type", ""))
    label = step.get("label") or module_id

    # Use saved positions if available; otherwise auto-layout
    saved_x = step.get("position_x") or step.get("positionX")
    saved_y = step.get("position_y") or step.get("positionY")
    if saved_x is not None and saved_y is not None:
        pos_x = saved_x
        pos_y = saved_y
    elif step_id in resource_node_ids:
        pos_x = INITIAL_X
        pos_y = INITIAL_Y
    elif step_id in iterate_target_to_loop:
        # Loop body — directly below loop node
        loop_id = iterate_target_to_loop[step_id]
        loop_idx = next((i for i, s in enumerate(main_flow_steps) if s.get("id") == loop_id), 0)
        pos_x = INITIAL_X + loop_idx * HORIZONTAL_SPACING
        pos_y = INITIAL_Y + 250
    elif step_id in done_target_to_loop:
        # Done target — right of loop node
        loop_id = done_target_to_loop[step_id]
        loop_idx = next((i for i, s in enumerate(main_flow_steps) if s.get("id") == loop_id), 0)
        pos_x = INITIAL_X + (loop_idx + 1) * HORIZONTAL_SPACING
        pos_y = INITIAL_Y
    else:
        main_idx = next((i for i, s in enumerate(main_flow_steps) if s.get("id") == step_id), index)
        pos_x = INITIAL_X + main_idx * HORIZONTAL_SPACING
        pos_y = INITIAL_Y

    # Handle params — filter against module's registered params_schema
    params = step.get("params") or step.get("config") or {}
    if isinstance(params, list):
        params_obj: Dict[str, Any] = {}
        for item in params:
            if isinstance(item, dict):
                params_obj.update(item)
        params = params_obj

    # Initialize connections for flow control nodes
    connections = step.get("connections")
    if is_loop_module(module_id):
        if not connections:
            connections = {"iterate": [], "done": []}
        # Populate iterate from params.target for backward compatibility
        # This ensures LoopNode.vue has the correct data for rendering
        if not connections.get("iterate") and params.get("target"):
            target = params.get("target")
            if target in step_id_map:
                connections["iterate"] = [target]
    elif is_branch_module(module_id) and not connections:
        connections = {"true": [], "false": []}

    return {
        "id": step_id,
        "type": "custom",
        "position": {"x": pos_x, "y": pos_y},
        "label": label,
        "data": build_step_node_data(step, module_id, label, params, connections),
    }


def _reposition_resource_nodes(
    nodes: List[Dict[str, Any]],
    resource_to_parent: Dict[str, Dict[str, str]],
) -> None:
    """Reposition resource nodes below their parent, centered horizontally.

    Mutates node positions in-place.
    """
    node_map = {n["id"]: n for n in nodes}
    for node in nodes:
        res_info = resource_to_parent.get(node["id"])
        if not res_info:
            continue
        parent_node = node_map.get(res_info["parentId"])
        if not parent_node:
            continue

        siblings = [
            {"nodeId": nid, "type": info["type"]}
            for nid, info in resource_to_parent.items()
            if info["parentId"] == res_info["parentId"]
        ]
        order = {"model": 0, "memory": 1, "tools": 2}
        siblings.sort(key=lambda s: order.get(s["type"], 99))

        my_index = next((i for i, s in enumerate(siblings) if s["nodeId"] == node["id"]), 0)
        total = len(siblings)
        total_width = (total - 1) * RESOURCE_SPACING
        start_x = parent_node["position"]["x"] - total_width / 2

        node["position"] = {
            "x": start_x + my_index * RESOURCE_SPACING,
            "y": parent_node["position"]["y"] + RESOURCE_Y_OFFSET,
        }
