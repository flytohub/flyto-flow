/**
 * Edge Design System
 *
 * High-tech flowing edge styling with glow effects.
 * Inspired by cinematic workflow visualizations.
 *
 * Key features:
 * - Dual-layer rendering (glow + core)
 * - Smooth bezier curves
 * - State-based glow intensity
 * - Animated flow particles
 */

// =============================================================================
// Color Palette
// =============================================================================

export const EDGE_COLORS = {
  // Primary flow color (purple/violet)
  primary: {
    core: '#8B5CF6',
    glow: 'rgba(139, 92, 246, 0.6)',
    glowIntense: 'rgba(139, 92, 246, 0.9)'
  },

  // Success/completed (emerald)
  success: {
    core: '#10B981',
    glow: 'rgba(16, 185, 129, 0.5)',
    glowIntense: 'rgba(16, 185, 129, 0.8)'
  },

  // Error (red)
  error: {
    core: '#EF4444',
    glow: 'rgba(239, 68, 68, 0.5)',
    glowIntense: 'rgba(239, 68, 68, 0.8)'
  },

  // Warning/loop (amber)
  warning: {
    core: '#F59E0B',
    glow: 'rgba(245, 158, 11, 0.5)',
    glowIntense: 'rgba(245, 158, 11, 0.8)'
  },

  // Info/resource (cyan)
  info: {
    core: '#06B6D4',
    glow: 'rgba(6, 182, 212, 0.5)',
    glowIntense: 'rgba(6, 182, 212, 0.8)'
  },

  // Branch true (green)
  branchTrue: {
    core: '#22C55E',
    glow: 'rgba(34, 197, 94, 0.5)',
    glowIntense: 'rgba(34, 197, 94, 0.8)'
  },

  // Branch false (slate)
  branchFalse: {
    core: '#64748B',
    glow: 'rgba(100, 116, 139, 0.4)',
    glowIntense: 'rgba(100, 116, 139, 0.7)'
  }
}

// =============================================================================
// Edge States
// =============================================================================

export const EDGE_STATES = {
  IDLE: 'idle',
  ACTIVE: 'active',
  EXECUTING: 'executing',
  COMPLETED: 'completed',
  ERROR: 'error',
  HOVER: 'hover',
  SELECTED: 'selected'
}

// =============================================================================
// Edge Style Presets
// =============================================================================

export const EDGE_STYLE_PRESETS = {
  // Default flow edge
  default: {
    coreWidth: 2.5,
    glowWidth: 4,
    glowBlur: 3,
    glowOpacity: 0.2,
    color: EDGE_COLORS.primary,
    animated: false,
    dashArray: null
  },

  // Active/executing edge
  active: {
    coreWidth: 3,
    glowWidth: 6,
    glowBlur: 4,
    glowOpacity: 0.4,
    color: EDGE_COLORS.primary,
    animated: true,
    dashArray: '8 4',
    animationDuration: '0.8s'
  },

  // Completed edge
  completed: {
    coreWidth: 2.5,
    glowWidth: 4,
    glowBlur: 3,
    glowOpacity: 0.25,
    color: EDGE_COLORS.success,
    animated: false,
    dashArray: null
  },

  // Error edge
  error: {
    coreWidth: 3,
    glowWidth: 6,
    glowBlur: 4,
    glowOpacity: 0.35,
    color: EDGE_COLORS.error,
    animated: true,
    dashArray: '6 3',
    animationDuration: '0.6s'
  },

  // Loop edge
  loop: {
    coreWidth: 2,
    glowWidth: 4,
    glowBlur: 3,
    glowOpacity: 0.25,
    color: EDGE_COLORS.warning,
    animated: true,
    dashArray: '5 5',
    animationDuration: '0.5s'
  },

  // Resource/data edge
  resource: {
    coreWidth: 1.5,
    glowWidth: 6,
    glowBlur: 3,
    glowOpacity: 0.3,
    color: EDGE_COLORS.info,
    animated: false,
    dashArray: '4 2'
  },

  // Hover state
  hover: {
    coreWidth: 3,
    glowWidth: 6,
    glowBlur: 4,
    glowOpacity: 0.4,
    animated: false
  },

  // Selected state
  selected: {
    coreWidth: 3.5,
    glowWidth: 8,
    glowBlur: 5,
    glowOpacity: 0.5,
    animated: false
  }
}

// =============================================================================
// SVG Filter Definitions
// =============================================================================

/**
 * Get SVG filter definitions for edge glow effects
 * These should be added to the SVG defs once per canvas
 */
export function getEdgeFilterDefs() {
  return `
    <!-- Edge glow filter - primary -->
    <filter id="edge-glow-primary" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur"/>
      <feColorMatrix in="blur" type="matrix"
        values="0.55 0 0 0 0
                0.36 0 0 0 0
                0.96 0 0 0 0
                0 0 0 0.6 0"/>
      <feMerge>
        <feMergeNode/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Edge glow filter - success -->
    <filter id="edge-glow-success" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur"/>
      <feColorMatrix in="blur" type="matrix"
        values="0.06 0 0 0 0
                0.73 0 0 0 0
                0.51 0 0 0 0
                0 0 0 0.5 0"/>
      <feMerge>
        <feMergeNode/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Edge glow filter - error -->
    <filter id="edge-glow-error" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur"/>
      <feColorMatrix in="blur" type="matrix"
        values="0.94 0 0 0 0
                0.27 0 0 0 0
                0.27 0 0 0 0
                0 0 0 0.6 0"/>
      <feMerge>
        <feMergeNode/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Edge glow filter - warning/loop -->
    <filter id="edge-glow-warning" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur"/>
      <feColorMatrix in="blur" type="matrix"
        values="0.96 0 0 0 0
                0.62 0 0 0 0
                0.04 0 0 0 0
                0 0 0 0.5 0"/>
      <feMerge>
        <feMergeNode/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Edge glow filter - info/resource -->
    <filter id="edge-glow-info" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur"/>
      <feColorMatrix in="blur" type="matrix"
        values="0.02 0 0 0 0
                0.71 0 0 0 0
                0.83 0 0 0 0
                0 0 0 0.4 0"/>
      <feMerge>
        <feMergeNode/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Edge glow filter - intense (for hover/selected) -->
    <filter id="edge-glow-intense" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Animated flow gradient -->
    <linearGradient id="edge-flow-gradient" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="currentColor" stop-opacity="0.2">
        <animate attributeName="offset" values="0;1" dur="1.5s" repeatCount="indefinite"/>
      </stop>
      <stop offset="30%" stop-color="currentColor" stop-opacity="1">
        <animate attributeName="offset" values="0.3;1.3" dur="1.5s" repeatCount="indefinite"/>
      </stop>
      <stop offset="60%" stop-color="currentColor" stop-opacity="0.2">
        <animate attributeName="offset" values="0.6;1.6" dur="1.5s" repeatCount="indefinite"/>
      </stop>
    </linearGradient>
  `
}

// =============================================================================
// Path Utilities
// =============================================================================

/**
 * Calculate control points for a smooth bezier curve
 * Creates organic flowing curves that don't look too mechanical
 */
export function calculateBezierControlPoints(sourceX, sourceY, targetX, targetY, options = {}) {
  const { curvature = 0.5, tension = 0.3 } = options

  const dx = targetX - sourceX
  const dy = targetY - sourceY
  const distance = Math.sqrt(dx * dx + dy * dy)

  // Horizontal offset based on distance
  const offsetX = Math.min(distance * curvature, 150)

  // Slight vertical variation for organic feel
  const offsetY = dy * tension

  return {
    cx1: sourceX + offsetX,
    cy1: sourceY + offsetY * 0.3,
    cx2: targetX - offsetX,
    cy2: targetY - offsetY * 0.3
  }
}

/**
 * Generate SVG path for a smooth bezier edge
 */
export function generateBezierPath(sourceX, sourceY, targetX, targetY, options = {}) {
  const { cx1, cy1, cx2, cy2 } = calculateBezierControlPoints(sourceX, sourceY, targetX, targetY, options)

  return `M ${sourceX} ${sourceY} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${targetX} ${targetY}`
}

/**
 * Generate SVG path for a smoothstep edge (horizontal-vertical-horizontal)
 */
export function generateSmoothstepPath(sourceX, sourceY, targetX, targetY, options = {}) {
  const { borderRadius = 8 } = options

  const dx = targetX - sourceX
  const midX = sourceX + dx / 2

  // Simple horizontal-vertical-horizontal path with rounded corners
  if (Math.abs(sourceY - targetY) < 10) {
    // Nearly horizontal - just use a straight line
    return `M ${sourceX} ${sourceY} L ${targetX} ${targetY}`
  }

  return `M ${sourceX} ${sourceY}
          L ${midX - borderRadius} ${sourceY}
          Q ${midX} ${sourceY}, ${midX} ${sourceY + Math.sign(targetY - sourceY) * borderRadius}
          L ${midX} ${targetY - Math.sign(targetY - sourceY) * borderRadius}
          Q ${midX} ${targetY}, ${midX + borderRadius} ${targetY}
          L ${targetX} ${targetY}`
}

// =============================================================================
// Animation Utilities
// =============================================================================

export const EDGE_ANIMATIONS = {
  // Flow animation - dashes moving along the path
  flow: {
    name: 'edge-flow',
    keyframes: `
      @keyframes edge-flow {
        from { stroke-dashoffset: 24; }
        to { stroke-dashoffset: 0; }
      }
    `,
    duration: '1s',
    timingFunction: 'linear',
    iterationCount: 'infinite'
  },

  // Pulse animation - glow intensity
  pulse: {
    name: 'edge-pulse',
    keyframes: `
      @keyframes edge-pulse {
        0%, 100% { opacity: 0.4; }
        50% { opacity: 0.8; }
      }
    `,
    duration: '2s',
    timingFunction: 'ease-in-out',
    iterationCount: 'infinite'
  },

  // Error reverse flow
  errorReverse: {
    name: 'edge-error-reverse',
    keyframes: `
      @keyframes edge-error-reverse {
        from { stroke-dashoffset: 0; }
        to { stroke-dashoffset: 18; }
      }
    `,
    duration: '0.6s',
    timingFunction: 'linear',
    iterationCount: 'infinite'
  }
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get style preset based on edge state and type
 */
export function getEdgeStyle(state = EDGE_STATES.IDLE, edgeType = 'default') {
  const basePreset = EDGE_STYLE_PRESETS[edgeType] || EDGE_STYLE_PRESETS.default

  // Apply state modifiers
  switch (state) {
    case EDGE_STATES.HOVER:
      return { ...basePreset, ...EDGE_STYLE_PRESETS.hover }
    case EDGE_STATES.SELECTED:
      return { ...basePreset, ...EDGE_STYLE_PRESETS.selected }
    case EDGE_STATES.EXECUTING:
      return { ...basePreset, ...EDGE_STYLE_PRESETS.active }
    case EDGE_STATES.COMPLETED:
      return { ...basePreset, ...EDGE_STYLE_PRESETS.completed }
    case EDGE_STATES.ERROR:
      return { ...basePreset, ...EDGE_STYLE_PRESETS.error }
    default:
      return basePreset
  }
}

/**
 * Get filter ID based on edge color type
 */
export function getGlowFilterId(colorType = 'primary') {
  const filterMap = {
    primary: 'edge-glow-primary',
    success: 'edge-glow-success',
    error: 'edge-glow-error',
    warning: 'edge-glow-warning',
    info: 'edge-glow-info',
    branchTrue: 'edge-glow-success',
    branchFalse: 'edge-glow-primary'
  }
  return filterMap[colorType] || 'edge-glow-primary'
}

export default {
  EDGE_COLORS,
  EDGE_STATES,
  EDGE_STYLE_PRESETS,
  EDGE_ANIMATIONS,
  getEdgeFilterDefs,
  calculateBezierControlPoints,
  generateBezierPath,
  generateSmoothstepPath,
  getEdgeStyle,
  getGlowFilterId
}
