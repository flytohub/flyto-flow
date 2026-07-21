"""
Phase 3: Merge detection (in-degree >= 2)
Phase 5: Merge node positioning (delayed, after branches are laid out)
"""

from collections import deque
from typing import Set

from services.template.layout.positioning import (
    _position_branch_children,
    _position_switch_children,
    _position_loop_children,
    _position_standard_children,
)


# ---------------------------------------------------------------------------
# Phase 3: Merge detection
# ---------------------------------------------------------------------------

def _detect_merge_nodes(parents_of: dict, children_of: dict) -> Set[str]:
    """Detect nodes with in-degree >= 2 (merge points)."""
    merge_nodes = set()
    for nid, parents in parents_of.items():
        if len(parents) >= 2:
            merge_nodes.add(nid)
    return merge_nodes


# ---------------------------------------------------------------------------
# Phase 5: Merge node positioning
# ---------------------------------------------------------------------------

def _position_merge_nodes(
    merge_nodes: set,
    parents_of: dict,
    children_of: dict,
    node_types: dict,
    loop_map: dict,
    edge_handles: dict,
    positions: dict,
    layers: dict,
    subtree_heights: dict,
    node_widths: dict,
    cfg: dict,
    subtree_depths: dict = None,
):
    """Position merge nodes after all branches are laid out, then continue BFS."""
    if not merge_nodes:
        return

    node_width = cfg["node_width"]
    node_height = cfg["node_height"]
    v_spacing = cfg["v_spacing"]
    branch_offset = cfg["branch_offset"]
    case_spacing = cfg["case_spacing"]
    edge_gap = cfg["edge_gap"]

    # Sort merge nodes by layer to process in order
    sorted_merges = sorted(merge_nodes, key=lambda nid: layers.get(nid, 0))

    visited_merges = set()
    for merge_id in sorted_merges:
        if merge_id in visited_merges:
            continue
        visited_merges.add(merge_id)

        parents = parents_of.get(merge_id, [])
        positioned_parents = [p for p in parents if p in positions]

        if not positioned_parents:
            positions[merge_id] = {
                "x": cfg["initial_x"],
                "y": cfg["initial_y"],
            }
            continue

        # X = rightmost (parent_x + parent_width) + edge_gap
        max_right_edge = max(
            positions[p]["x"] + node_widths.get(p, node_width)
            for p in positioned_parents
        )
        merge_x = max_right_edge + edge_gap

        # Y = median of parent Y values
        parent_ys = sorted([positions[p]["y"] for p in positioned_parents])
        if len(parent_ys) % 2 == 1:
            merge_y = parent_ys[len(parent_ys) // 2]
        else:
            mid = len(parent_ys) // 2
            merge_y = (parent_ys[mid - 1] + parent_ys[mid]) / 2

        positions[merge_id] = {"x": merge_x, "y": merge_y}

        # Continue BFS from merge node to position its downstream nodes
        queue = deque([merge_id])
        visited_bfs = {merge_id}
        while queue:
            nid = queue.popleft()
            if nid not in positions:
                continue

            px = positions[nid]["x"]
            py = positions[nid]["y"]
            ntype = node_types.get(nid, "standard")
            children = children_of.get(nid, [])

            # Skip nodes whose children are all already positioned or are merge nodes
            unpositioned = [c for c in children if c not in positions and c not in merge_nodes]
            if not unpositioned:
                continue

            # Edge-to-edge spacing
            parent_w = node_widths.get(nid, node_width)
            child_x = px + parent_w + edge_gap

            # Dispatch ONCE per node based on node type
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
                _position_standard_children(
                    nid, children, positions, subtree_heights,
                    child_x, py, v_spacing, node_height, merge_nodes, queue
                )

            # Mark newly positioned children as visited for this BFS
            for child in children:
                if child not in visited_bfs and child in positions:
                    visited_bfs.add(child)
                    queue.append(child)
