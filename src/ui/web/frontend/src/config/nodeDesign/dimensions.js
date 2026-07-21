/**
 * Node Design System — Dimensions
 * NODE, HANDLE, BUTTON, BADGE config objects
 */

// =============================================================================
// NODE DIMENSIONS
// Static defaults — backend SSOT overrides via CSS variables (--node-{type}-width/height)
// See: /api/config/node-design + stores/config/actions.js _injectNodeDesignCSSVars()
// =============================================================================

export const NODE = {
  // Standard node dimensions (rectangle) — fallback values
  width: 240,
  height: 76,  // IMPORTANT: Height must be consistent for horizontal connections

  // Shape variants - includes precise handle positioning
  // handleOffset: Distance from handle center to container edge (negative = outside)
  shapes: {
    // Rectangle: Handle 6px outside edge
    rectangle: {
      width: 240,
      height: 76,
      borderRadius: 16,
      handleOffset: -6
    },

    // Square: Handle 6px outside edge
    square: {
      width: 76,
      height: 76,
      borderRadius: 12,
      handleOffset: -6
    },

    // Circle: Diameter = container height, handle aligns with circumference
    circle: {
      width: 76,
      height: 76,
      borderRadius: '50%',
      handleOffset: -6
    },

    // Diamond: Inner square rotated 45deg, vertices align with container edges
    // Math: diagonal = 76px, side = 76/sqrt(2) = 54px
    diamond: {
      width: 76,
      height: 76,
      innerSize: 54,
      innerBorderRadius: 8,
      transform: 'rotate(45deg)',
      handleOffset: -6
    },

    // Hexagon: Vertices at container edges
    hexagon: {
      width: 88,
      height: 76,
      clipPath: 'polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)',
      handleOffset: -6
    },

    // Oval: Handle aligns with ellipse edge
    oval: {
      width: 120,
      height: 76,
      borderRadius: '50%',
      handleOffset: -6
    },

    // Pill: Semi-circles on left/right
    pill: {
      width: 160,
      height: 76,
      borderRadius: 38,  // height / 2 = perfect semi-circle
      handleOffset: -6
    },

    // Semi-circle: Rounded left, flat right (for trigger nodes)
    semicircle: {
      width: 120,
      height: 76,
      borderRadius: '38px 0 0 38px',  // Only left side rounded
      handleOffset: -6
    },

    // Semi-circle right: Flat left, rounded right
    semicircleRight: {
      width: 120,
      height: 76,
      borderRadius: '0 38px 38px 0',  // Only right side rounded
      handleOffset: -6
    },

    // Container node (larger)
    container: {
      width: 90,
      height: 90,  // Note: Exception, not 76
      borderRadius: 14,
      handleOffset: -6
    }
  },

  // Compact/collapsed node dimensions
  compact: {
    width: 64,
    height: 64,
  },

  // Card styles
  card: {
    borderWidth: 2,
    borderRadius: 16,
    padding: '12px 16px',
    gap: 12,
    background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
    shadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
    shadowHover: '0 8px 24px',
    transition: 'all 0.2s ease'
  },

  // Hover effect
  hoverTransform: 'translateY(-2px)'
}

// =============================================================================
// HANDLE (Connection Points)
// =============================================================================

export const HANDLE = {
  // Standard sizes
  size: 12,
  sizeSmall: 10,   // Flow control nodes
  sizeLarge: 14,   // AI Agent main handle
  sizeTiny: 8,     // AI Agent sub handles

  // Border
  borderWidth: 2,
  borderColor: '#374151',

  // Position offset
  offset: 6,

  // Position configurations
  positions: {
    left: { left: '-6px', top: '50%', transform: 'translateY(-50%)' },
    right: { right: '-6px', top: '50%', transform: 'translateY(-50%)' },
    top: { top: '-5px', left: '50%', transform: 'translateX(-50%)' },
    bottom: { bottom: '-5px', left: '50%', transform: 'translateX(-50%)' }
  },

  // Colors
  colors: {
    default: '#6B7280',
    success: '#10B981',
    error: '#EF4444',
    loop: '#F59E0B',
    blue: '#3B82F6',
    purple: '#8B5CF6'
  },

  // Border colors (matching colors above)
  borderColors: {
    default: '#374151',
    success: '#059669',
    error: '#DC2626',
    loop: '#B45309',
    blue: '#2563EB',
    purple: '#6D28D9'
  },

  // Hover effect
  hoverScale: 1.2,
  transition: 'all 0.2s ease'
}

// =============================================================================
// BUTTONS
// =============================================================================

export const BUTTON = {
  // Delete button
  delete: {
    size: 24,
    sizeSmall: 18,
    sizeMedium: 20,
    position: { top: '-8px', left: '-8px' },
    positionRight: { top: '-8px', right: '-8px' },
    borderRadius: '50%',
    borderWidth: 2,
    borderColor: '#1F2937',
    background: '#EF4444',
    backgroundHover: '#DC2626',
    color: 'white',
    iconSize: 14,
    opacity: 0,
    opacityHover: 1,
    zIndex: 20,
    transition: 'all 0.2s ease',
    hoverScale: 1.2
  },

  // Add button
  add: {
    size: 36,
    sizeSmall: 28,
    sizeSub: 34,
    borderRadius: '50%',
    borderWidth: 3,
    borderColor: '#1F2937',
    color: 'white',
    iconSize: 16,
    iconSizeSmall: 14,
    opacity: 0,
    opacityHover: 1,
    zIndex: 10,
    transition: 'all 0.2s ease',
    hoverScale: 1.15,

    // Position variants
    positions: {
      right: { right: '-20px', top: '50%', transform: 'translateY(-50%)' },
      rightSmall: { right: '-16px', top: '50%', transform: 'translateY(-50%)' },
      bottom: { bottom: '-16px', left: '50%', transform: 'translateX(-50%)' },
      top: { top: '-16px', left: '50%', transform: 'translateX(-50%)' }
    },

    // Hover position adjustments
    hoverPositions: {
      right: { right: '-18px' },
      rightSmall: { right: '-14px' },
      bottom: { bottom: '-14px' },
      top: { top: '-14px' }
    }
  }
}

// =============================================================================
// CATEGORY BADGE
// =============================================================================

export const BADGE = {
  position: { top: '-8px', right: '12px' },
  padding: '2px 8px',
  borderRadius: '8px',
  fontSize: '9px',
  fontWeight: 700,
  textTransform: 'uppercase',
  color: 'white'
}
