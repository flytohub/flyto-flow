"""
Phase 4: Type-aware BFS positioning.

Positions nodes using BFS traversal with type-specific strategies
for branch, switch, loop, and standard nodes.
"""

from collections import deque
from typing import Dict, Optional

from services.template.layout.constants import (
    _find_child_by_handle,
    _effective_case_spacing,
)


def _position_nodes(
    control_node_ids: list,
    children_of: dict,
    parents_of: dict,
    node_types: dict,
    loop_map: dict,
    edge_handles: dict,
    layers: dict,
    subtree_heights: dict,
    merge_nodes: set,
    node_widths: dict,
    cfg: dict,
    subtree_depths: dict = None,
) -> Dict[str, Dict[str, float]]:
    """BFS-based positioning with type-specific strategies."""
    positions = {}
    visited = set()

    initial_x = cfg["initial_x"]
    initial_y = cfg["initial_y"]
    v_spacing = cfg["v_spacing"]
    node_width = cfg["node_width"]
    node_height = cfg["node_height"]
    branch_offset = cfg["branch_offset"]
    case_spacing = cfg["case_spacing"]
    edge_gap = cfg["edge_gap"]

    # Find start nodes (no parents in control flow)
    start_nodes = [nid for nid in control_node_ids if not parents_of.get(nid)]
    if not start_nodes:
        # Fallback: use nodes in layer 0
        start_nodes = [nid for nid in control_node_ids if layers.get(nid, 0) == 0]
    if not start_nodes and control_node_ids:
        start_nodes = [control_node_ids[0]]

    # Position start nodes vertically stacked
    y_cursor = initial_y
    for sid in start_nodes:
        positions[sid] = {"x": initial_x, "y": y_cursor}
        h = subtree_heights.get(sid, node_height)
        y_cursor += h + v_spacing

    queue = deque(start_nodes)

    while queue:
        nid = queue.popleft()
        if nid in visited:
            continue
        visited.add(nid)

        if nid not in positions:
            continue

        px = positions[nid]["x"]
        py = positions[nid]["y"]
        ntype = node_types.get(nid, "standard")
        children = children_of.get(nid, [])

        # Edge-to-edge: child_x = parent_x + parent_actual_width + gap
        parent_w = node_widths.get(nid, node_width)
        child_x = px + parent_w + edge_gap

        if ntype == "branch":
            _position_branch_children(
                nid, children, edge_handles, positions, subtree_heights,
                child_x, py, branch_offset, merge_nodes, queue
            )

        elif ntype == "switch":
            _position_switch_children(
                nid, children, edge_handles, positions, subtree_heights,
                child_x, py, case_spacing, merge_nodes, queue, cfg
            )

        elif ntype == "loop" and nid in loop_map:
            _position_loop_children(
                nid, loop_map[nid], positions, node_widths, node_width,
                child_x, py, v_spacing, node_height, merge_nodes, queue,
                edge_gap, subtree_depths=subtree_depths, cfg=cfg
            )

        else:
            # Standard node: single child same Y, multiple children stacked
            _position_standard_children(
                nid, children, positions, subtree_heights,
                child_x, py, v_spacing, node_height, merge_nodes, queue
            )

    return positions


def _position_branch_children(
    parent_id, children, edge_handles, positions, subtree_heights,
    child_x, parent_y, branch_offset, merge_nodes, queue
):
    """Position branch true/false children symmetrically."""
    true_child = _find_child_by_handle(parent_id, children, edge_handles, "true")
    false_child = _find_child_by_handle(parent_id, children, edge_handles, "false")

    h_true = subtree_heights.get(true_child, 76) if true_child else 76
    h_false = subtree_heights.get(false_child, 76) if false_child else 76
    gap = max(40, branch_offset / 3)

    if true_child and true_child not in merge_nodes:
        if true_child not in positions:
            true_y = parent_y - h_false / 2 - gap / 2
            positions[true_child] = {"x": child_x, "y": true_y}
        queue.append(true_child)

    if false_child and false_child not in merge_nodes:
        if false_child not in positions:
            false_y = parent_y + h_true / 2 + gap / 2
            positions[false_child] = {"x": child_x, "y": false_y}
        queue.append(false_child)

    # Other children (shouldn't happen for branch, but handle gracefully)
    for child in children:
        if child not in (true_child, false_child) and child not in merge_nodes:
            if child not in positions:
                positions[child] = {"x": child_x, "y": parent_y}
            queue.append(child)


def _position_switch_children(
    parent_id, children, edge_handles, positions, subtree_heights,
    child_x, parent_y, case_spacing, merge_nodes, queue, cfg
):
    """Position switch cases in a centered fan layout."""
    # Filter out merge nodes
    placeable = [c for c in children if c not in merge_nodes]
    if not placeable:
        return

    # Dynamic spacing: shrink when many cases, floor at min_case_spacing
    effective_spacing = _effective_case_spacing(len(placeable), cfg)

    # Calculate total height needed
    case_heights = [subtree_heights.get(c, cfg["node_height"]) for c in placeable]
    total_height = sum(case_heights) + effective_spacing * (len(placeable) - 1)

    # Center around parent_y
    y_cursor = parent_y - total_height / 2

    for i, child in enumerate(placeable):
        ch = case_heights[i]
        if child not in positions:
            positions[child] = {"x": child_x, "y": y_cursor}
        y_cursor += ch + effective_spacing
        queue.append(child)

    # Minimum Y protection: ensure no case node goes above y=20
    min_y = min(positions[c]["y"] for c in placeable if c in positions)
    if min_y < 20:
        shift = 20 - min_y
        for c in placeable:
            if c in positions:
                positions[c]["y"] += shift


def _position_loop_children(
    parent_id, loop_entry, positions, node_widths, default_width,
    child_x, parent_y, v_spacing, node_height, merge_nodes, queue,
    edge_gap, subtree_depths=None, cfg=None
):
    """Position loop body below and done to the right."""
    body_child = loop_entry.get("body")
    done_child = loop_entry.get("done")

    if body_child and body_child not in merge_nodes:
        if body_child not in positions:
            # Body goes below the loop node (same x, y + spacing)
            positions[body_child] = {
                "x": positions[parent_id]["x"],
                "y": parent_y + v_spacing,
            }
        queue.append(body_child)

    if done_child and done_child not in merge_nodes:
        if done_child not in positions:
            done_x = child_x  # Default: to the right of parent
            # If body has a horizontal chain, push done_x past it
            if body_child and subtree_depths and cfg:
                body_depth = subtree_depths.get(body_child, 1)
                h_spacing = cfg.get("h_spacing", 320)
                body_chain_right = positions[parent_id]["x"] + body_depth * h_spacing
                done_x = max(done_x, body_chain_right + edge_gap)
            positions[done_child] = {"x": done_x, "y": parent_y}
        queue.append(done_child)


def _position_standard_children(
    parent_id, children, positions, subtree_heights,
    child_x, parent_y, v_spacing, node_height, merge_nodes, queue
):
    """Position standard node children."""
    placeable = [c for c in children if c not in merge_nodes]
    if not placeable:
        return

    if len(placeable) == 1:
        child = placeable[0]
        if child not in positions:
            positions[child] = {"x": child_x, "y": parent_y}
        queue.append(child)
        return

    # Multiple children: stack vertically centered on parent
    child_heights = [subtree_heights.get(c, node_height) for c in placeable]
    total = sum(child_heights) + v_spacing * (len(placeable) - 1)
    y_cursor = parent_y - total / 2

    for i, child in enumerate(placeable):
        ch = child_heights[i]
        if child not in positions:
            positions[child] = {"x": child_x, "y": y_cursor}
        y_cursor += ch + v_spacing
        queue.append(child)
