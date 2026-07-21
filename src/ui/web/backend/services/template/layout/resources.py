"""
Phase 8: Resource node positioning
Phase 9: Orphan node positioning
Phase 10: Direction flip (RIGHT -> DOWN)
"""

from collections import defaultdict


# ---------------------------------------------------------------------------
# Phase 8: Resource node positioning
# ---------------------------------------------------------------------------

def _position_resource_nodes(
    resource_edges: list,
    positions: dict,
    node_map: dict,
    cfg: dict,
    node_widths: dict = None,
):
    """Position resource nodes centered below their parent.

    Resource nodes (AISubNode: Model/Memory/Tools) are ~100px wide,
    NOT the standard 240px. Using node_width would push them far left.
    """
    default_parent_width = cfg["node_width"]
    resource_node_width = cfg.get("resource_node_width", 100)
    resource_gap = cfg["resource_gap"]
    resource_offset = cfg["resource_offset"]

    # Build parent -> resource children map
    parent_resources = defaultdict(list)
    for e in resource_edges:
        parent_id = e.get("target")
        child_id = e.get("source")
        parent_resources[parent_id].append(child_id)

    for parent_id, child_ids in parent_resources.items():
        parent_pos = positions.get(parent_id)
        if not parent_pos:
            continue

        # Use actual parent width instead of hardcoded node_width
        parent_w = (node_widths.get(parent_id, default_parent_width)
                    if node_widths else default_parent_width)

        total_width = len(child_ids) * resource_node_width + (len(child_ids) - 1) * resource_gap
        # Center the resource group under the parent node
        parent_center_x = parent_pos["x"] + parent_w / 2
        start_x = parent_center_x - total_width / 2

        for i, child_id in enumerate(child_ids):
            positions[child_id] = {
                "x": start_x + i * (resource_node_width + resource_gap),
                "y": parent_pos["y"] + resource_offset,
            }


# ---------------------------------------------------------------------------
# Phase 9: Orphan nodes
# ---------------------------------------------------------------------------

def _position_orphans(control_node_ids: list, positions: dict, cfg: dict):
    """Position any unpositioned control nodes in a grid below the main flow."""
    orphans = [nid for nid in control_node_ids if nid not in positions]
    if not orphans:
        return

    node_width = cfg["node_width"]
    h_spacing = cfg["h_spacing"]
    v_spacing = cfg["v_spacing"]
    max_width = cfg["orphan_max_width"]

    # Find the bottom of existing layout
    if positions:
        max_y = max(p["y"] for p in positions.values())
        base_y = max_y + v_spacing * 2
    else:
        base_y = cfg["initial_y"]

    base_x = cfg["initial_x"]
    x_cursor = base_x
    y_cursor = base_y
    col_width = node_width + h_spacing

    for orphan in orphans:
        if x_cursor - base_x + node_width > max_width:
            x_cursor = base_x
            y_cursor += v_spacing

        positions[orphan] = {"x": x_cursor, "y": y_cursor}
        x_cursor += col_width


# ---------------------------------------------------------------------------
# Phase 10: Direction flip
# ---------------------------------------------------------------------------

def _apply_direction_flip(positions: dict):
    """Swap X and Y for DOWN direction."""
    for nid in positions:
        x = positions[nid]["x"]
        y = positions[nid]["y"]
        positions[nid] = {"x": y, "y": x}
