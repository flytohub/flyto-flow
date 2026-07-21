/**
 * Design Tokens - Animation & Transitions
 * Timing, easing, and duration constants
 */

export const ANIMATION = Object.freeze({
  // Durations (milliseconds)
  DURATION: {
    INSTANT: 0,
    FAST: 150,
    NORMAL: 200,
    SLOW: 300,
    SLOWER: 500,
    SLOWEST: 800,
  },

  // Easing functions
  EASING: {
    LINEAR: 'linear',
    EASE: 'ease',
    EASE_IN: 'ease-in',
    EASE_OUT: 'ease-out',
    EASE_IN_OUT: 'ease-in-out',
    // Custom cubic bezier
    SPRING: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
    BOUNCE: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    SMOOTH: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },

  // Pre-built transitions
  TRANSITION: {
    FAST: '150ms ease',
    NORMAL: '200ms ease',
    SLOW: '300ms ease',
    TRANSFORM: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
    OPACITY: '150ms ease-out',
    COLOR: '100ms ease',
  },

  // Delays (milliseconds)
  DELAY: {
    TOOLTIP: 300,
    HOVER: 100,
    STAGGER: 50,
  },
})

/**
 * Build a CSS transition string
 * @param {string[]} properties - CSS properties to transition
 * @param {number} duration - Duration in ms
 * @param {string} easing - Easing function
 * @returns {string} CSS transition value
 */
export function buildTransition(properties, duration = 200, easing = 'ease') {
  return properties.map(prop => `${prop} ${duration}ms ${easing}`).join(', ')
}
