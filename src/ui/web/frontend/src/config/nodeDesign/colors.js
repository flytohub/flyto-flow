/**
 * Node Design System — Colors
 * COLORS, GRADIENTS, STATES config objects
 */

// =============================================================================
// COLORS
// =============================================================================

export const COLORS = {
  // Primary
  primary: {
    purple: '#8B5CF6',
    purpleLight: '#A78BFA',
    purpleLighter: '#C4B5FD',
    purpleDark: '#6D28D9'
  },

  // Functional
  functional: {
    success: '#10B981',
    successDark: '#059669',
    error: '#EF4444',
    errorDark: '#DC2626',
    warning: '#F59E0B',
    warningDark: '#D97706',
    info: '#3B82F6',
    infoDark: '#2563EB'
  },

  // Node-specific colors
  nodes: {
    trigger: { main: '#F59E0B', dark: '#D97706' },
    branch: { true: '#10B981', false: '#EF4444' },
    loop: { body: '#3B82F6', done: '#10B981', back: '#F59E0B' },
    switch: { main: '#EC4899', light: '#F472B6', default: '#6B7280' },
    fork: { main: '#06B6D4', light: '#22D3EE' },
    container: { main: '#8B5CF6', layer: 'rgba(139, 92, 246, 0.1)' },
    aiAgent: { main: '#8B5CF6', glow: 'rgba(139, 92, 246, 0.3)' }
  },

  // Background
  background: {
    card: '#1e293b',
    cardDark: '#0f172a',
    darkest: '#0F172A'
  },

  // Border
  border: {
    default: '#334155',
    dark: '#1F2937',
    handle: '#374151'
  },

  // Text
  text: {
    primary: '#F1F5F9',
    secondary: '#9CA3AF',
    tertiary: '#64748B',
    muted: '#475569'
  }
}

// =============================================================================
// GRADIENTS
// =============================================================================

export const GRADIENTS = {
  // Button gradients
  buttons: {
    purple: 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
    green: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
    red: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
    orange: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
    blue: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
    cyan: 'linear-gradient(135deg, #06B6D4 0%, #0891B2 100%)',
    pink: 'linear-gradient(135deg, #EC4899 0%, #DB2777 100%)',
    gray: 'linear-gradient(135deg, #6B7280 0%, #4B5563 100%)'
  },

  // Card background gradients
  cards: {
    default: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
    aiAgent: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%)'
  },

  // Selected state border gradients
  selectedBorder: {
    default: 'linear-gradient(90deg, #8B5CF6, #06B6D4, #EC4899, #8B5CF6)',
    trigger: 'linear-gradient(90deg, #F59E0B, #EF4444, #F59E0B)',
    branch: 'linear-gradient(90deg, #8B5CF6, #A78BFA, #8B5CF6)',
    loop: 'linear-gradient(90deg, #F59E0B, #FBBF24, #F59E0B)',
    switch: 'linear-gradient(90deg, #EC4899, #F472B6, #EC4899)',
    fork: 'linear-gradient(90deg, #06B6D4, #22D3EE, #06B6D4)',
    container: 'linear-gradient(90deg, #8B5CF6, #A78BFA, #C4B5FD, #8B5CF6)'
  }
}

// =============================================================================
// STATES
// =============================================================================

export const STATES = {
  // Selected state
  selected: {
    borderColor: 'transparent',
    pseudoBefore: {
      inset: '-2px',
      borderRadius: '18px',
      padding: '2px',
      backgroundSize: '300% 100%'
    }
  },

  // Execution states
  execution: {
    running: {
      borderColor: '#8B5CF6',
      animation: 'running-pulse 1.5s ease-in-out infinite'
    },
    completed: {
      borderColor: '#10B981'
    },
    pending: {
      opacity: 0.8
    },
    error: {
      borderColor: '#EF4444'
    }
  },

  // Checkpoint state
  checkpoint: {
    borderColor: '#EF4444',
    rippleColor: '#EF4444',
    rippleAnimation: 'ripple-ring 2.5s ease-out infinite'
  },

  // Dimmed state
  dimmed: {
    opacity: 0.4,
    pointerEvents: 'none'
  },

  // Flow control state
  flowControl: {
    borderStyle: 'dashed'
  }
}
