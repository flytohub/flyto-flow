"""
Main layout engine entry point + Phase 0 (parse input).

10-phase pipeline:
  0. Parse input (classify edges, build adjacency)
  1. Layer assignment (longest-path via Kahn's algorithm)
  2. Subtree height estimation (bottom-up)
  3. Merge detection (in-degree >= 2 from different paths)
  4. Type-aware positioning (branch/switch/loop/standard)
  5. Merge node positioning (delayed)
  6. Crossing minimization (barycenter heuristic)
  7. Overlap resolution (AABB push-apart)
  8. Resource node positioning
  9. Orphan node positioning
 10. Direction flip (RIGHT -> DOWN)
"""

from collections import defaultdict
from typing import Dict, List, Any

from services.graph_helpers import get_node_type_from_module
from services.node_config import get_node_dimensions
from config.layout import LAYOUT_CONFIG, PRESETS

from services.template.layout.constants import (
    _get_source_handle,
    _get_target_handle,
    _get_edge_data_type,
)
from services.template.layout.layers import (
    _assign_layers,
    _estimate_subtree_height,
    _estimate_subtree_depth,
)
from services.template.layout.positioning import _position_nodes
from services.template.layout.merge import _detect_merge_nodes, _position_merge_nodes
from services.template.layout.crossing import _minimize_crossings
from services.template.layout.overlap import _resolve_overlaps
from services.template.layout.resources import (
    _position_resource_nodes,
    _position_orphans,
    _apply_direction_flip,
)


def compute_layout_positions(
    workflow_dict: dict,
    preset: str = "default",
    direction: str = "RIGHT",
) -> dict:
    """
    Compute smart auto-layout positions for workflow nodes.

    Args:
        workflow_dict: Workflow with nodes/edges
        preset: Layout preset (default | compact | spacious)
        direction: Layout direction (RIGHT | DOWN)

    Returns:
        {"positions": {node_id: {"x": int, "y": int}, ...}}
    """
    preset_cfg = PRESETS.get(preset, PRESETS["default"])
    cfg = {
        "initial_x": LAYOUT_CONFIG["initial_x"],
        "initial_y": LAYOUT_CONFIG["initial_y"],
        "h_spacing": preset_cfg["h_spacing"],
        "v_spacing": preset_cfg["v_spacing"],
        "node_width": LAYOUT_CONFIG["node_width"],
        "node_height": LAYOUT_CONFIG["node_height"],
        "compact_width": LAYOUT_CONFIG.get("compact_width", 64),
        "trigger_width": LAYOUT_CONFIG.get("trigger_width", 120),
        "resource_gap": LAYOUT_CONFIG["resource_gap"],
        "resource_offset": LAYOUT_CONFIG["resource_offset"],
        "resource_node_width": LAYOUT_CONFIG.get("resource_node_width", 100),
        "branch_offset": preset_cfg.get("branch_offset", LAYOUT_CONFIG["branch_offset"]),
        "case_spacing": preset_cfg.get("case_spacing", LAYOUT_CONFIG["case_spacing"]),
        "min_case_spacing": LAYOUT_CONFIG.get("min_case_spacing", 60),
        "edge_gap": LAYOUT_CONFIG["edge_gap"],
        "min_node_gap": LAYOUT_CONFIG["min_node_gap"],
        "orphan_max_width": LAYOUT_CONFIG["orphan_max_width"],
        "crossing_sweeps": LAYOUT_CONFIG["crossing_sweeps"],
        "overlap_max_iter": LAYOUT_CONFIG["overlap_max_iter"],
    }

    nodes = workflow_dict.get("nodes", [])
    edges = workflow_dict.get("edges", [])
    if not nodes:
        return {"positions": {}}

    # Phase 0: Parse input
    parsed = _parse_input(nodes, edges)
    node_map = parsed["node_map"]
    node_types = parsed["node_types"]
    resource_edges = parsed["resource_edges"]
    children_of = parsed["children_of"]
    parents_of = parsed["parents_of"]
    loop_map = parsed["loop_map"]
    edge_handles = parsed["edge_handles"]
    control_node_ids = parsed["control_node_ids"]

    # Build per-node width map (edge-to-edge aware)
    node_widths = {}
    for nid in control_node_ids:
        node_widths[nid] = _get_node_width(node_map.get(nid, {}), node_types.get(nid, "standard"), cfg)

    # Phase 1: Layer assignment
    layers = _assign_layers(control_node_ids, children_of, parents_of, loop_map)

    # Phase 2: Subtree height estimation
    subtree_heights = {}
    for nid in control_node_ids:
        if nid not in subtree_heights:
            _estimate_subtree_height(
                nid, children_of, node_types, loop_map, edge_handles, subtree_heights, cfg
            )

    # Phase 2.5: Subtree depth estimation (horizontal chain depth)
    subtree_depths = {}
    for nid in control_node_ids:
        if nid not in subtree_depths:
            _estimate_subtree_depth(nid, children_of, loop_map, subtree_depths)

    # Phase 3: Detect merge nodes
    merge_nodes = _detect_merge_nodes(parents_of, children_of)

    # Phase 4: Type-aware positioning
    positions = _position_nodes(
        control_node_ids, children_of, parents_of, node_types,
        loop_map, edge_handles, layers, subtree_heights, merge_nodes,
        node_widths, cfg, subtree_depths
    )

    # Phase 5: Position merge nodes
    _position_merge_nodes(merge_nodes, parents_of, children_of, node_types,
                          loop_map, edge_handles, positions, layers,
                          subtree_heights, node_widths, cfg, subtree_depths)

    # Phase 6: Crossing minimization
    _minimize_crossings(layers, positions, parents_of, children_of, loop_map, cfg, node_types)

    # Phase 7: Overlap resolution
    _resolve_overlaps(positions, node_widths, cfg)

    # Phase 8: Resource node positioning
    _position_resource_nodes(resource_edges, positions, node_map, cfg, node_widths)

    # Phase 8.5: Add resource node widths and re-run overlap resolution
    for e in resource_edges:
        child_id = e.get("source")
        if child_id and child_id not in node_widths:
            node_widths[child_id] = cfg.get("resource_node_width", 100)
    _resolve_overlaps(positions, node_widths, cfg)

    # Phase 9: Orphan nodes
    _position_orphans(control_node_ids, positions, cfg)

    # Phase 10: Direction flip
    if direction == "DOWN":
        _apply_direction_flip(positions)

    # Round all positions to integers
    for nid in positions:
        positions[nid] = {
            "x": int(round(positions[nid]["x"])),
            "y": int(round(positions[nid]["y"])),
        }

    return {"positions": positions}


# ---------------------------------------------------------------------------
# Phase 0: Parse input
# ---------------------------------------------------------------------------

def _parse_input(nodes: list, edges: list) -> dict:
    """Classify edges, build adjacency, detect node types."""
    node_map = {}
    node_types = {}
    for n in nodes:
        nid = n.get("id")
        module_id = (
            n.get("module_id")
            or n.get("data", {}).get("module")
            or n.get("data", {}).get("module_id")
            or ""
        )
        node_map[nid] = n
        node_types[nid] = get_node_type_from_module(module_id)

    # Identify resource nodes: node data (primary) + edge metadata (fallback)
    # Note: frontend HTTP client converts camelCase -> snake_case, so check both
    resource_node_ids = set()
    for n in nodes:
        nid = n.get("id")
        data = n.get("data") or {}
        if data.get("isSubNode") or data.get("is_sub_node"):
            resource_node_ids.add(nid)

    # Fallback: also check edge metadata for legacy data without isSubNode
    for e in edges:
        edge_data = e.get("data") or {}
        edge_data_type = _get_edge_data_type(edge_data)
        target_handle = _get_target_handle(e)
        if edge_data_type == "resource" or target_handle in ("target-model", "target-memory", "target-tools"):
            src = e.get("source")
            if src:
                resource_node_ids.add(src)

    # Classify edges using resource_node_ids
    resource_edges = []
    loop_edges = []
    control_edges = []

    for e in edges:
        src = e.get("source")
        tgt = e.get("target")
        if src in resource_node_ids or tgt in resource_node_ids:
            resource_edges.append(e)
        elif _is_loop_edge(e):
            loop_edges.append(e)
        else:
            control_edges.append(e)

    control_node_ids = [n.get("id") for n in nodes if n.get("id") not in resource_node_ids]

    # Build adjacency (control edges only)
    children_of = defaultdict(list)
    parents_of = defaultdict(list)
    edge_handles = {}  # (source, target) -> sourceHandle

    for e in control_edges:
        src = e.get("source")
        tgt = e.get("target")
        if src in resource_node_ids or tgt in resource_node_ids:
            continue
        children_of[src].append(tgt)
        parents_of[tgt].append(src)
        handle = _get_source_handle(e)
        edge_handles[(src, tgt)] = handle

    # Build loop_map: loop_node_id -> {"body": child_id, "done": child_id}
    loop_map = _build_loop_map(control_edges, loop_edges, node_types, edge_handles)

    # Back-fill adjacency for loop body/done that came from loop_edges.
    # _is_loop_edge matches "loop" in sourceHandle, so edges like
    # "source-loop-body" get classified as loop_edges and the body node
    # ends up with no parent in children_of/parents_of -> treated as start node.
    for loop_id, entry in loop_map.items():
        for role in ("body", "done"):
            child = entry.get(role)
            if not child:
                continue
            if child not in children_of.get(loop_id, []):
                children_of[loop_id].append(child)
            if loop_id not in parents_of.get(child, []):
                parents_of[child].append(loop_id)
            if (loop_id, child) not in edge_handles:
                # Find actual handle from loop_edges
                actual_handle = f"source-{role}"
                for e in loop_edges:
                    if e.get("source") == loop_id and e.get("target") == child:
                        actual_handle = _get_source_handle(e)
                        break
                edge_handles[(loop_id, child)] = actual_handle

    return {
        "node_map": node_map,
        "node_types": node_types,
        "control_edges": control_edges,
        "resource_edges": resource_edges,
        "resource_node_ids": resource_node_ids,
        "children_of": children_of,
        "parents_of": parents_of,
        "loop_map": loop_map,
        "edge_handles": edge_handles,
        "control_node_ids": control_node_ids,
    }


def _get_node_width(node_dict: dict, node_type: str, cfg: dict) -> float:
    """Determine actual pixel width based on node type and state.

    Priority:
      1. data.collapsed -> compact_width (64px)
      2. NODE_TYPE_CONFIGS dimensions (per-type SSOT)
      3. cfg["node_width"] fallback (240px)
    """
    data = node_dict.get("data") or {}
    ui_state = node_dict.get("ui_state") or data.get("ui_state") or {}

    if data.get("collapsed") or ui_state.get("collapsed"):
        return cfg["compact_width"]

    dims = get_node_dimensions(node_type)
    return dims.get("width", cfg["node_width"])


def _is_loop_edge(e: dict) -> bool:
    """Check if an edge represents a loop connection (body or done handle)."""
    edge_type = (e.get("type") or "").lower()
    edge_data = e.get("data") or {}
    edge_data_type = _get_edge_data_type(edge_data)
    source_handle = _get_source_handle(e)
    target_handle = _get_target_handle(e)
    return (
        edge_type == "loop"
        or edge_data_type in ("loop", "iterate")
        or "loop" in source_handle
        or "loop" in target_handle
    )


def _build_loop_map(control_edges, loop_edges, node_types, edge_handles):
    """Build loop_map: loop_id -> {body: child_id, done: child_id}."""
    loop_map = {}

    for nid, ntype in node_types.items():
        if ntype != "loop":
            continue
        loop_map[nid] = {"body": None, "done": None}

    # From control edges with sourceHandle hints
    for e in control_edges:
        src = e.get("source")
        if src not in loop_map:
            continue
        handle = _get_source_handle(e).lower()
        tgt = e.get("target")
        if "body" in handle or "item" in handle or "iterate" in handle:
            loop_map[src]["body"] = tgt
        elif "done" in handle or "complete" in handle:
            loop_map[src]["done"] = tgt

    # From loop edges (body_out -> body start)
    for e in loop_edges:
        src = e.get("source")
        tgt = e.get("target")
        handle = _get_source_handle(e).lower()
        # Loop-back: body_end -> loop node (type=loop)
        if tgt in loop_map:
            # This is a loop-back edge, skip
            pass
        elif src in loop_map:
            if "body" in handle or "item" in handle or "iterate" in handle:
                loop_map[src]["body"] = tgt
            elif "done" in handle:
                loop_map[src]["done"] = tgt

    # For loops with children but no explicit handle mapping, use heuristic:
    # If a loop has exactly 2 children and one isn't assigned, assign by context
    for nid in loop_map:
        entry = loop_map[nid]
        if entry["body"] is None or entry["done"] is None:
            # Look at all children of this loop
            all_children = []
            for e in control_edges:
                if e.get("source") == nid:
                    all_children.append(e.get("target"))
            assigned = {entry["body"], entry["done"]} - {None}
            unassigned = [c for c in all_children if c not in assigned]
            if entry["body"] is None and unassigned:
                entry["body"] = unassigned[0]
                unassigned = unassigned[1:]
            if entry["done"] is None and unassigned:
                entry["done"] = unassigned[0]

    return loop_map
