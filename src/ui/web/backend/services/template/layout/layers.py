"""
Phase 1: Layer assignment (longest-path via Kahn's algorithm)
Phase 2: Subtree height/depth estimation (bottom-up, memoized)
"""

from collections import defaultdict, deque
from typing import Dict, Optional

from services.template.layout.constants import (
    _find_child_by_handle,
    _effective_case_spacing,
)


# ---------------------------------------------------------------------------
# Phase 1: Layer assignment (longest-path)
# ---------------------------------------------------------------------------

def _assign_layers(
    node_ids: list,
    children_of: dict,
    parents_of: dict,
    loop_map: dict,
) -> Dict[str, int]:
    """Assign layer to each node using longest-path via Kahn's algorithm."""
    id_set = set(node_ids)
    in_degree = defaultdict(int)
    for nid in id_set:
        in_degree[nid] = 0
    for nid in id_set:
        for child in children_of.get(nid, []):
            if child in id_set:
                in_degree[child] += 1

    # Kahn's
    queue = deque()
    for nid in id_set:
        if in_degree[nid] == 0:
            queue.append(nid)

    layers = {}
    for nid in id_set:
        layers[nid] = 0

    topo_order = []
    while queue:
        nid = queue.popleft()
        topo_order.append(nid)
        for child in children_of.get(nid, []):
            if child not in id_set:
                continue
            # Longest-path: layer[child] = max(layer[child], layer[nid] + 1)
            # But for loop body children, they go DOWN not RIGHT, so same layer offset
            is_loop_body = False
            if nid in loop_map and loop_map[nid].get("body") == child:
                is_loop_body = True

            if is_loop_body:
                # Loop body: same layer as loop (positioned below, not to the right)
                candidate = layers[nid]
            else:
                candidate = layers[nid] + 1

            if candidate > layers.get(child, 0):
                layers[child] = candidate

            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    # Handle cycle leftovers (shouldn't happen in DAGs, but be safe)
    for nid in id_set:
        if nid not in layers:
            layers[nid] = 0

    return layers


# ---------------------------------------------------------------------------
# Phase 2: Subtree height estimation (bottom-up, memoized)
# ---------------------------------------------------------------------------

def _estimate_subtree_height(
    nid: str,
    children_of: dict,
    node_types: dict,
    loop_map: dict,
    edge_handles: dict,
    cache: dict,
    cfg: dict,
    _visiting: Optional[set] = None,
) -> float:
    """Recursively estimate vertical space needed for a node's subtree."""
    if nid in cache:
        return cache[nid]

    # Cycle protection
    if _visiting is None:
        _visiting = set()
    if nid in _visiting:
        return cfg["node_height"]
    _visiting.add(nid)

    ntype = node_types.get(nid, "standard")
    node_h = cfg["node_height"]
    v_spacing = cfg["v_spacing"]
    branch_offset = cfg["branch_offset"]

    children = children_of.get(nid, [])
    if not children:
        cache[nid] = node_h
        _visiting.discard(nid)
        return node_h

    if ntype == "branch":
        true_child = _find_child_by_handle(nid, children, edge_handles, "true")
        false_child = _find_child_by_handle(nid, children, edge_handles, "false")

        h_true = node_h
        h_false = node_h
        if true_child:
            h_true = _estimate_subtree_height(
                true_child, children_of, node_types, loop_map, edge_handles, cache, cfg, _visiting
            )
        if false_child:
            h_false = _estimate_subtree_height(
                false_child, children_of, node_types, loop_map, edge_handles, cache, cfg, _visiting
            )
        gap = max(40, branch_offset / 3)
        total = h_true + h_false + gap
        cache[nid] = total
        _visiting.discard(nid)
        return total

    if ntype == "switch":
        case_heights = []
        for child in children:
            ch = _estimate_subtree_height(
                child, children_of, node_types, loop_map, edge_handles, cache, cfg, _visiting
            )
            case_heights.append(ch)
        if case_heights:
            total = sum(case_heights) + _effective_case_spacing(len(children), cfg) * (len(case_heights) - 1)
        else:
            total = node_h
        cache[nid] = total
        _visiting.discard(nid)
        return total

    if ntype == "loop" and nid in loop_map:
        body_child = loop_map[nid].get("body")
        done_child = loop_map[nid].get("done")
        h_body = node_h
        h_done = node_h
        if body_child:
            h_body = _estimate_subtree_height(
                body_child, children_of, node_types, loop_map, edge_handles, cache, cfg, _visiting
            )
        if done_child:
            h_done = _estimate_subtree_height(
                done_child, children_of, node_types, loop_map, edge_handles, cache, cfg, _visiting
            )
        total = max(node_h + v_spacing + h_body, h_done)
        cache[nid] = total
        _visiting.discard(nid)
        return total

    # Standard: single child pass-through, multi-child sum
    if len(children) == 1:
        h_child = _estimate_subtree_height(
            children[0], children_of, node_types, loop_map, edge_handles, cache, cfg, _visiting
        )
        result = max(node_h, h_child)
        cache[nid] = result
        _visiting.discard(nid)
        return result

    total = 0
    for child in children:
        total += _estimate_subtree_height(
            child, children_of, node_types, loop_map, edge_handles, cache, cfg, _visiting
        )
    total += v_spacing * (len(children) - 1)
    cache[nid] = total
    _visiting.discard(nid)
    return total


def _estimate_subtree_depth(
    nid: str,
    children_of: dict,
    loop_map: dict,
    cache: dict,
    _visiting: Optional[set] = None,
) -> int:
    """Count max horizontal chain depth from nid (how many layers go RIGHT)."""
    if nid in cache:
        return cache[nid]

    if _visiting is None:
        _visiting = set()
    if nid in _visiting:
        return 0
    _visiting.add(nid)

    children = children_of.get(nid, [])
    if not children:
        cache[nid] = 1
        _visiting.discard(nid)
        return 1

    # Skip loop body children (they go DOWN, not RIGHT)
    right_children = [c for c in children
                      if not (nid in loop_map and loop_map[nid].get("body") == c)]
    if not right_children:
        cache[nid] = 1
        _visiting.discard(nid)
        return 1

    result = 1 + max(_estimate_subtree_depth(c, children_of, loop_map, cache, _visiting)
                      for c in right_children)
    cache[nid] = result
    _visiting.discard(nid)
    return result
