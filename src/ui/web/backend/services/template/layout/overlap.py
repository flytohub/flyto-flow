"""
Phase 7: Overlap resolution (AABB collision detection with bidirectional push-apart).
"""


def _resolve_overlaps(positions: dict, node_widths: dict, cfg: dict):
    """AABB collision detection with bidirectional push-apart.

    Strategy:
    1. Collect ALL overlapping pairs and sort by overlap area (largest first)
    2. For each pair, choose the direction (X or Y) requiring smaller push
    3. Split the push between BOTH nodes (bidirectional) to avoid cascade
       where pushing B right squashes B into C
    """
    max_iter = cfg["overlap_max_iter"]
    node_w = cfg["node_width"]
    node_h = cfg["node_height"]
    min_gap = cfg["min_node_gap"]

    node_ids = list(positions.keys())
    if len(node_ids) < 2:
        return

    for iteration in range(max_iter):
        # Collect all overlaps first, then sort by area (largest first)
        overlaps = []
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                a = node_ids[i]
                b = node_ids[j]
                pa = positions[a]
                pb = positions[b]

                w_a = node_widths.get(a, node_w)
                w_b = node_widths.get(b, node_w)

                overlap_x = min(pa["x"] + w_a, pb["x"] + w_b) - max(pa["x"], pb["x"])
                overlap_y = min(pa["y"] + node_h, pb["y"] + node_h) - max(pa["y"], pb["y"])

                if overlap_x > 0 and overlap_y > 0:
                    overlaps.append((overlap_x * overlap_y, a, b, w_a, w_b))

        if not overlaps:
            break

        # Process largest overlaps first to stabilize layout
        overlaps.sort(reverse=True)

        for _, a, b, w_a, w_b in overlaps:
            pa = positions[a]
            pb = positions[b]

            # Recompute overlap (positions may have shifted from earlier fixes)
            ov_x = min(pa["x"] + w_a, pb["x"] + w_b) - max(pa["x"], pb["x"])
            ov_y = min(pa["y"] + node_h, pb["y"] + node_h) - max(pa["y"], pb["y"])

            if ov_x <= 0 or ov_y <= 0:
                continue  # Already resolved by earlier push

            need_push_x = ov_x + min_gap
            need_push_y = ov_y + min_gap

            if need_push_x <= need_push_y:
                # Push right node further right (unidirectional)
                if pa["x"] <= pb["x"]:
                    pb["x"] += need_push_x
                else:
                    pa["x"] += need_push_x
            else:
                # Push lower node further down (unidirectional)
                if pa["y"] <= pb["y"]:
                    pb["y"] += need_push_y
                else:
                    pa["y"] += need_push_y
