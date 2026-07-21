/**
 * Custom Edge Components
 *
 * High-tech flowing edges with glow effects.
 */

export { default as GlowEdge } from './GlowEdge.vue'

// Edge type identifiers for VueFlow registration
export const EDGE_TYPES = {
  GLOW: 'glow',
  GLOW_BEZIER: 'glowBezier',
  GLOW_SMOOTHSTEP: 'glowSmoothstep'
}
