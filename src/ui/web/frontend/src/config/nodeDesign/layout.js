/**
 * Node Design System — Layout
 * LAYOUT, Z_INDEX config objects
 */

// =============================================================================
// Z-INDEX LAYERS
// =============================================================================
//
// Layer hierarchy (lower = behind, higher = in front):
//
//   Layer 0   : Effect pseudo-elements (::before for glow/border effects)
//   Layer 1   : Card base (.node-card, .trigger-card, etc.)
//   Layer 2   : Card content (icons, text, inner elements)
//   Layer 5   : Handles (connection points)
//   Layer 10  : Add buttons
//   Layer 15  : Badges & indicators (category badge, status indicators)
//   Layer 20  : Delete buttons (topmost interactive element)
//   Layer 30  : Tooltips & popovers
//   Layer 100 : Modals & overlays
//
// Usage in CSS:
//   z-index: var(--z-card);  OR  z-index: 1;  (use Z_INDEX.card in JS)
//
// =============================================================================

export const Z_INDEX = {
  // Base layers
  effectBefore: 0,     // ::before pseudo-element for effects (glow, border animation)
  card: 1,             // Main card element
  cardContent: 2,      // Content inside card (icons, text)

  // Interactive elements
  handle: 5,           // Connection handles
  addButton: 10,       // Add node buttons

  // Overlays on node
  badge: 15,           // Category badge (TRIGGER, BRANCH, etc.)
  indicator: 15,       // Status indicators (running, error dots)
  statusIcon: 15,      // Execution status icons

  // Top layer interactive
  deleteButton: 20,    // Delete button (always accessible)

  // Floating elements
  tooltip: 30,         // Tooltips
  popover: 35,         // Popovers & dropdowns
  contextMenu: 40,     // Context menus

  // Global overlays
  modal: 100,          // Modal dialogs
  notification: 110,   // Toast notifications
  debug: 999           // Debug overlays
}

// =============================================================================
// LAYOUT - Canvas spacing and positioning rules
// =============================================================================
//
// IMPORTANT: Spacing should be calculated EDGE-TO-EDGE, not center-to-center
// This ensures visual consistency regardless of node width.
//
// Formula: nextNodeX = currentNodeX + currentNodeWidth + EDGE_GAP
//
// Example with EDGE_GAP = 80:
//   Semicircle (120px) -> Rectangle (240px)
//   nextX = 0 + 120 + 80 = 200  (rectangle starts at x=200)
//
//   Rectangle (240px) -> Diamond (76px)
//   nextX = 200 + 240 + 80 = 520  (diamond starts at x=520)
//
// =============================================================================

export const LAYOUT = {
  // Canvas grid settings
  grid: {
    size: 20,           // Grid snap size (px)
    enabled: true,      // Enable grid snapping
    visible: false      // Show grid lines
  },

  // Initial position for first node
  initial: {
    x: 100,
    y: 150
  },

  // Edge-to-edge gaps (not center-to-center!)
  spacing: {
    // Horizontal gap between node RIGHT edge and next node LEFT edge
    horizontal: 80,     // Gap between sequential nodes

    // Vertical spacing
    vertical: 100,      // Gap between parallel branches

    // Branch-specific
    branchOffset: 120,  // Vertical offset for true/false paths from center

    // Multi-output (Switch, Fork)
    caseSpacing: 100,   // Vertical spacing between switch cases

    // Loop-specific
    loopBodyOffset: 150,  // Vertical offset for loop body
    loopBackMargin: 40,   // Margin for loop-back edge routing

    // Resource nodes (AI Agent sub-nodes)
    resourceGap: 60,      // Horizontal gap between Model/Memory/Tools
    resourceOffset: 160   // Vertical offset below parent agent
  },

  // Connection/Edge routing
  connection: {
    // Edge types
    defaultType: 'smoothstep',    // 'straight' | 'smoothstep' | 'step' | 'bezier'
    loopType: 'smoothstep',       // Loop-back edges always curved

    // Curve settings (for smoothstep/bezier)
    borderRadius: 8,              // Corner radius for step edges
    curvature: 0.25,              // Bezier curve intensity (0-1)

    // Edge offset from handle
    edgeOffset: 0,                // Gap between handle center and edge start

    // Minimum edge length before curving
    minSegmentLength: 20
  },

  // Handle connection rules
  handleConnection: {
    // Snap distance for connecting handles
    snapRadius: 30,

    // Valid connection directions
    // left->right, top->bottom are standard flow
    // right->left, bottom->top are loop-back
    allowedDirections: {
      source: ['right', 'bottom'],
      target: ['left', 'top']
    }
  },

  // Multi-output node rules
  multiOutput: {
    // Branch (if/else)
    branch: {
      truePosition: 'right',      // Handle position for true
      falsePosition: 'bottom',    // Handle position for false
      trueOffset: { x: 0, y: -120 },   // True child relative to parent
      falseOffset: { x: 0, y: 120 }    // False child relative to parent
    },

    // Switch (multi-case)
    switch: {
      maxVisibleCases: 6,         // Show scroll after this many
      casePosition: 'right',      // Handle position for cases
      defaultPosition: 'bottom',  // Handle position for default
      // Children centered around parent Y
      // Formula: startY = parentY - ((caseCount - 1) * caseSpacing) / 2
      centerAlign: true
    },

    // Loop
    loop: {
      bodyPosition: 'right',      // Handle for loop body
      donePosition: 'bottom',     // Handle for loop done
      backPosition: 'top',        // Handle for loop-back input
      bodyOffset: { x: 80, y: 150 },   // Body child position
      doneOffset: { x: 80, y: 0 }      // Done child position (same Y)
    },

    // Fork (parallel)
    fork: {
      branchPosition: 'right',
      // Spread evenly, similar to switch
      centerAlign: true
    },

    // AI Agent (resource nodes)
    aiAgent: {
      resourcePosition: 'bottom', // Handles for Model/Memory/Tools
      // Resources spread horizontally below agent
      resourceLayout: 'horizontal',
      resourceOffset: { x: 0, y: 120 }
    }
  },

  // Auto-layout algorithm settings
  autoLayout: {
    // Direction: 'LR' (left-to-right) or 'TB' (top-to-bottom)
    direction: 'LR',

    // Alignment within same depth
    alignment: 'center',    // 'top' | 'center' | 'bottom'

    // Handle orphan nodes (no connections)
    orphanPlacement: 'below',  // 'below' | 'right' | 'grid'
    orphanOffset: { x: 0, y: 200 },

    // Animation when repositioning
    animate: true,
    animationDuration: 300
  }
}
