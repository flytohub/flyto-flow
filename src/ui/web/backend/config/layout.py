"""
Layout Configuration

Unified layout constants aligned with frontend nodeDesignSystem.js.
Single source of truth for all layout computations.
"""

# Layout constants aligned with frontend nodeDesignSystem.js
LAYOUT_CONFIG = {
    "initial_x": 100,           # nodeDesignSystem LAYOUT.initial.x
    "initial_y": 150,           # nodeDesignSystem LAYOUT.initial.y
    "horizontal_spacing": 320,  # NODE.width(240) + LAYOUT.spacing.horizontal(80)
    "vertical_spacing": 140,    # LAYOUT.spacing.vertical(64) + NODE.height(76)
    "node_width": 240,          # NODE.width
    "node_height": 76,          # NODE.height
    "resource_gap": 60,         # LAYOUT.spacing.resourceGap
    "resource_offset": 160,     # LAYOUT.spacing.resourceOffset
    "resource_node_width": 100, # AISubNode visual width (~72px card + padding)
    "compact_width": 64,        # Collapsed node width
    "trigger_width": 120,       # Trigger/terminal semicircle width
    "branch_offset": 120,       # Y offset for branch true/false paths
    "edge_gap": 80,             # Gap between node edge and next node
    "case_spacing": 120,        # Vertical spacing between switch cases
    "min_case_spacing": 60,     # Minimum case spacing (prevents negative Y with many cases)
    "min_node_gap": 20,         # Minimum gap between nodes (overlap prevention)
    "min_branch_gap": 40,       # Minimum vertical gap between branch true/false paths
    "orphan_max_width": 1200,   # Max width before orphan nodes wrap
    "crossing_sweeps": 6,       # Number of barycenter sweep passes
    "overlap_max_iter": 10,     # Max iterations for overlap resolution
}

# Layout presets
PRESETS = {
    "default": {
        "h_spacing": 320,
        "v_spacing": 140,
        "branch_offset": 120,
        "case_spacing": 120,
    },
    "compact": {
        "h_spacing": 260,
        "v_spacing": 120,
        "branch_offset": 90,
        "case_spacing": 90,
    },
    "spacious": {
        "h_spacing": 400,
        "v_spacing": 220,
        "branch_offset": 160,
        "case_spacing": 160,
    },
}
