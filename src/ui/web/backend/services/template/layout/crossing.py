"""
Phase 6: Crossing minimization (barycenter heuristic).
"""

from collections import defaultdict, deque


def _minimize_crossings(
    layers: dict,
    positions: dict,
    parents_of: dict,
    children_of: dict,
    loop_map: dict,
    cfg: dict,
    node_types: dict = None,
):
    """Barycenter heuristic: reorder nodes within each layer to reduce crossings."""
    sweeps = cfg["crossing_sweeps"]
    node_height = cfg["node_height"]
    min_gap = cfg["min_node_gap"]

    # Collect loop body nodes AND all their descendants -- these are positioned
    # vertically relative to their loop parent and must NOT be reordered.
    # Protecting only the direct body node is insufficient; descendants would
    # get reordered and break the visual loop structure.
    loop_subtree_nodes = set()
    for loop_id, entry in loop_map.items():
        body = entry.get("body")
        if body:
            # BFS to collect all descendants of the loop body
            q = deque([body])
            while q:
                nid = q.popleft()
                if nid in loop_subtree_nodes:
                    continue
                loop_subtree_nodes.add(nid)
                for child in children_of.get(nid, []):
                    if child not in loop_subtree_nodes:
                        q.append(child)

    # Collect switch direct case children -- these are positioned by
    # _position_switch_children and must NOT be reordered by barycenter.
    # Only protect the first-layer case entry nodes, not their downstream.
    switch_case_nodes = set()
    if node_types:
        for nid, ntype in node_types.items():
            if ntype == "switch":
                for child in children_of.get(nid, []):
                    switch_case_nodes.add(child)

    # Group nodes by layer, excluding loop subtree + switch case nodes
    layer_nodes = defaultdict(list)
    for nid, layer in layers.items():
        if nid in positions and nid not in loop_subtree_nodes and nid not in switch_case_nodes:
            layer_nodes[layer].append(nid)

    max_layer = max(layer_nodes.keys()) if layer_nodes else 0

    for sweep in range(sweeps):
        if sweep % 2 == 0:
            # Forward sweep: order by parent Y average
            for layer_idx in range(1, max_layer + 1):
                nodes_in_layer = layer_nodes.get(layer_idx, [])
                if len(nodes_in_layer) <= 1:
                    continue

                # Compute barycenter for each node
                barycenters = {}
                for nid in nodes_in_layer:
                    parents = [p for p in parents_of.get(nid, []) if p in positions]
                    if parents:
                        barycenters[nid] = sum(positions[p]["y"] for p in parents) / len(parents)
                    else:
                        barycenters[nid] = positions[nid]["y"]

                # Sort by barycenter, tiebreak by current Y to preserve Phase 4 order
                sorted_nodes = sorted(
                    nodes_in_layer,
                    key=lambda n: (barycenters[n], positions[n]["y"])
                )

                _reassign_y_positions(sorted_nodes, positions, node_height, min_gap)
        else:
            # Backward sweep: order by children Y average
            for layer_idx in range(max_layer - 1, -1, -1):
                nodes_in_layer = layer_nodes.get(layer_idx, [])
                if len(nodes_in_layer) <= 1:
                    continue

                barycenters = {}
                for nid in nodes_in_layer:
                    children = [c for c in children_of.get(nid, []) if c in positions]
                    if children:
                        barycenters[nid] = sum(positions[c]["y"] for c in children) / len(children)
                    else:
                        barycenters[nid] = positions[nid]["y"]

                sorted_nodes = sorted(
                    nodes_in_layer,
                    key=lambda n: (barycenters[n], positions[n]["y"])
                )
                _reassign_y_positions(sorted_nodes, positions, node_height, min_gap)


def _reassign_y_positions(sorted_nodes, positions, node_height, min_gap):
    """Reassign Y positions based on barycenter targets with minimum spacing."""
    if len(sorted_nodes) <= 1:
        return

    min_spacing = node_height + min_gap + 4
    # Use the median Y of sorted nodes as the center
    target_ys = [positions[nid]["y"] for nid in sorted_nodes]
    center = sum(target_ys) / len(target_ys)
    total_height = min_spacing * (len(sorted_nodes) - 1)
    y_start = center - total_height / 2
    for i, nid in enumerate(sorted_nodes):
        positions[nid]["y"] = y_start + i * min_spacing
