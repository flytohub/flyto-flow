/**
 * Node Design System — Animations
 * ANIMATIONS, SHAPE_EFFECTS, TRANSITIONS config objects
 */

// =============================================================================
// ANIMATIONS
// =============================================================================

export const ANIMATIONS = {
  // Selected state border flow
  borderFlow: {
    name: 'border-flow',
    duration: '3s',
    timing: 'linear',
    iteration: 'infinite',
    keyframes: `
      @keyframes border-flow {
        0% { background-position: 0% 50%; }
        100% { background-position: 300% 50%; }
      }
    `
  },

  // Running state pulse
  runningPulse: {
    name: 'running-pulse',
    duration: '1.5s',
    timing: 'ease-in-out',
    iteration: 'infinite',
    keyframes: `
      @keyframes running-pulse {
        0%, 100% { box-shadow: 0 0 0 2px rgba(var(--pulse-color), 0.3); }
        50% { box-shadow: 0 0 0 4px rgba(var(--pulse-color), 0.4); }
      }
    `
  },

  // Checkpoint ripple
  rippleRing: {
    name: 'ripple-ring',
    duration: '2.5s',
    timing: 'ease-out',
    iteration: 'infinite',
    keyframes: `
      @keyframes ripple-ring {
        0% { transform: scale(1); opacity: 0.6; }
        100% { transform: scale(1.3); opacity: 0; }
      }
    `
  },

  // Gradient shift (AI Agent)
  gradientShift: {
    name: 'gradient-shift',
    duration: '4s',
    timing: 'ease',
    iteration: 'infinite',
    keyframes: `
      @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
      }
    `
  },

  // Spin (Loading)
  spin: {
    name: 'spin',
    duration: '1s',
    timing: 'linear',
    iteration: 'infinite',
    keyframes: `
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
    `
  }
}

// =============================================================================
// SHAPE EFFECTS - Complete animation specifications per shape
// =============================================================================

export const SHAPE_EFFECTS = {
  // effectType: 'border' = animated border (mask technique), 'glow' = box-shadow glow
  // Shapes with complex borders (semicircle, diamond, hexagon) use glow effects

  rectangle: {
    borderRadius: '16px',
    outerRadius: '18px',
    effectType: 'border',  // Standard border animation works well
    selected: {
      type: 'border-flow',
      gradient: 'linear-gradient(90deg, #8B5CF6, #06B6D4, #EC4899, #8B5CF6)',
      duration: '3s'
    },
    checkpoint: {
      type: 'ripple',
      color: '#EF4444',
      duration: '2.5s'
    },
    running: {
      type: 'pulse',
      color: 'rgba(139, 92, 246, 0.4)'
    }
  },

  square: {
    borderRadius: '12px',
    outerRadius: '14px',
    effectType: 'border',
    selected: {
      type: 'border-flow',
      gradient: 'linear-gradient(90deg, #8B5CF6, #06B6D4, #EC4899, #8B5CF6)',
      duration: '3s'
    },
    checkpoint: {
      type: 'ripple',
      color: '#EF4444',
      duration: '2.5s'
    },
    running: {
      type: 'pulse',
      color: 'rgba(139, 92, 246, 0.4)'
    }
  },

  circle: {
    borderRadius: '50%',
    outerRadius: '50%',
    effectType: 'border',
    selected: {
      type: 'border-flow',
      gradient: 'linear-gradient(90deg, #8B5CF6, #06B6D4, #EC4899, #8B5CF6)',
      duration: '3s'
    },
    checkpoint: {
      type: 'ripple',
      color: '#EF4444',
      duration: '2.5s'
    },
    running: {
      type: 'pulse',
      color: 'rgba(139, 92, 246, 0.4)'
    }
  },

  oval: {
    borderRadius: '50%',
    outerRadius: '50%',
    effectType: 'border',
    selected: {
      type: 'border-flow',
      gradient: 'linear-gradient(90deg, #8B5CF6, #06B6D4, #EC4899, #8B5CF6)',
      duration: '3s'
    },
    checkpoint: {
      type: 'ripple',
      color: '#EF4444',
      duration: '2.5s'
    },
    running: {
      type: 'pulse',
      color: 'rgba(139, 92, 246, 0.4)'
    }
  },

  pill: {
    borderRadius: '38px',
    outerRadius: '40px',
    effectType: 'border',
    selected: {
      type: 'border-flow',
      gradient: 'linear-gradient(90deg, #8B5CF6, #06B6D4, #EC4899, #8B5CF6)',
      duration: '3s'
    },
    checkpoint: {
      type: 'ripple',
      color: '#EF4444',
      duration: '2.5s'
    },
    running: {
      type: 'pulse',
      color: 'rgba(139, 92, 246, 0.4)'
    }
  },

  // ============ Special shapes - use glow effects ============

  semicircle: {
    borderRadius: '38px 0 0 38px',
    outerRadius: '40px 0 0 40px',
    effectType: 'glow',  // Glow works better for asymmetric shapes
    selected: {
      type: 'glow-pulse',
      colors: ['#F59E0B', '#FBBF24'],
      shadows: {
        base: '0 0 0 2px #F59E0B, 0 0 20px rgba(245, 158, 11, 0.6), 0 0 40px rgba(245, 158, 11, 0.3)',
        peak: '0 0 0 3px #FBBF24, 0 0 30px rgba(245, 158, 11, 0.8), 0 0 60px rgba(245, 158, 11, 0.4)'
      },
      duration: '1.5s'
    },
    checkpoint: {
      type: 'glow-pulse',
      colors: ['#EF4444', '#F87171'],
      shadows: {
        base: '0 0 0 2px #EF4444, 0 0 15px rgba(239, 68, 68, 0.5)',
        peak: '0 0 0 4px #EF4444, 0 0 30px rgba(239, 68, 68, 0.7), 0 0 50px rgba(239, 68, 68, 0.3)'
      },
      duration: '1.5s'
    },
    running: {
      type: 'glow-pulse',
      colors: ['#8B5CF6', '#A78BFA'],
      shadows: {
        base: '0 0 0 2px #8B5CF6, 0 0 15px rgba(139, 92, 246, 0.5)',
        peak: '0 0 0 3px #A78BFA, 0 0 25px rgba(139, 92, 246, 0.7)'
      },
      duration: '1.5s'
    }
  },

  semicircleRight: {
    borderRadius: '0 38px 38px 0',
    outerRadius: '0 40px 40px 0',
    effectType: 'glow',
    selected: {
      type: 'glow-pulse',
      colors: ['#10B981', '#34D399'],
      shadows: {
        base: '0 0 0 2px #10B981, 0 0 20px rgba(16, 185, 129, 0.6), 0 0 40px rgba(16, 185, 129, 0.3)',
        peak: '0 0 0 3px #34D399, 0 0 30px rgba(16, 185, 129, 0.8), 0 0 60px rgba(16, 185, 129, 0.4)'
      },
      duration: '1.5s'
    },
    checkpoint: {
      type: 'glow-pulse',
      colors: ['#EF4444', '#F87171'],
      shadows: {
        base: '0 0 0 2px #EF4444, 0 0 15px rgba(239, 68, 68, 0.5)',
        peak: '0 0 0 4px #EF4444, 0 0 30px rgba(239, 68, 68, 0.7), 0 0 50px rgba(239, 68, 68, 0.3)'
      },
      duration: '1.5s'
    },
    running: {
      type: 'glow-pulse',
      colors: ['#8B5CF6', '#A78BFA'],
      shadows: {
        base: '0 0 0 2px #8B5CF6, 0 0 15px rgba(139, 92, 246, 0.5)',
        peak: '0 0 0 3px #A78BFA, 0 0 25px rgba(139, 92, 246, 0.7)'
      },
      duration: '1.5s'
    }
  },

  diamond: {
    borderRadius: '8px',
    outerRadius: '10px',
    innerSize: 54,
    transform: 'rotate(45deg)',
    effectType: 'glow',  // Glow avoids rotation issues
    selected: {
      type: 'glow-pulse',
      colors: ['#EC4899', '#F472B6'],
      shadows: {
        base: '0 0 0 2px #EC4899, 0 0 20px rgba(236, 72, 153, 0.6), 0 0 40px rgba(236, 72, 153, 0.3)',
        peak: '0 0 0 3px #F472B6, 0 0 30px rgba(236, 72, 153, 0.8), 0 0 60px rgba(236, 72, 153, 0.4)'
      },
      duration: '1.5s'
    },
    checkpoint: {
      type: 'glow-pulse',
      colors: ['#EF4444', '#F87171'],
      shadows: {
        base: '0 0 0 2px #EF4444, 0 0 15px rgba(239, 68, 68, 0.5)',
        peak: '0 0 0 4px #EF4444, 0 0 30px rgba(239, 68, 68, 0.7), 0 0 50px rgba(239, 68, 68, 0.3)'
      },
      duration: '1.5s'
    },
    running: {
      type: 'glow-pulse',
      colors: ['#8B5CF6', '#A78BFA'],
      shadows: {
        base: '0 0 0 2px #8B5CF6, 0 0 15px rgba(139, 92, 246, 0.5)',
        peak: '0 0 0 3px #A78BFA, 0 0 25px rgba(139, 92, 246, 0.7)'
      },
      duration: '1.5s'
    }
  },

  hexagon: {
    clipPath: 'polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)',
    outerClipPath: 'polygon(23% -2%, 77% -2%, 102% 50%, 77% 102%, 23% 102%, -2% 50%)',
    effectType: 'glow',  // clip-path doesn't work with border animations
    selected: {
      type: 'filter-glow',
      colors: ['#06B6D4', '#22D3EE'],
      filters: {
        base: 'drop-shadow(0 0 8px rgba(6, 182, 212, 0.6))',
        peak: 'drop-shadow(0 0 15px rgba(6, 182, 212, 0.8)) drop-shadow(0 0 30px rgba(6, 182, 212, 0.4))'
      },
      duration: '1.5s'
    },
    checkpoint: {
      type: 'filter-glow',
      colors: ['#EF4444', '#F87171'],
      filters: {
        base: 'drop-shadow(0 0 8px rgba(239, 68, 68, 0.6))',
        peak: 'drop-shadow(0 0 15px rgba(239, 68, 68, 0.8)) drop-shadow(0 0 30px rgba(239, 68, 68, 0.4))'
      },
      duration: '1.5s'
    },
    running: {
      type: 'filter-glow',
      colors: ['#8B5CF6', '#A78BFA'],
      filters: {
        base: 'drop-shadow(0 0 6px rgba(139, 92, 246, 0.5))',
        peak: 'drop-shadow(0 0 12px rgba(139, 92, 246, 0.7))'
      },
      duration: '1.5s'
    }
  },

  container: {
    borderRadius: '14px',
    outerRadius: '16px',
    effectType: 'border',
    selected: {
      type: 'border-flow',
      gradient: 'linear-gradient(90deg, #8B5CF6, #A78BFA, #C4B5FD, #8B5CF6)',
      duration: '3s'
    },
    checkpoint: {
      type: 'ripple',
      color: '#EF4444',
      duration: '2.5s'
    },
    running: {
      type: 'pulse',
      color: 'rgba(139, 92, 246, 0.4)'
    }
  }
}

// =============================================================================
// TRANSITIONS
// =============================================================================

export const TRANSITIONS = {
  fast: 'all 0.15s ease',
  default: 'all 0.2s ease',
  smooth: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
  spring: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)'
}
