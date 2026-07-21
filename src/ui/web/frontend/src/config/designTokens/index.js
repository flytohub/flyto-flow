/**
 * Design Tokens - Main Export
 * Centralized configuration for all UI constants
 */

export { SPACING, toRem, toEm } from './spacing'
export { LAYOUT } from './layout'
export { ANIMATION, buildTransition } from './animation'
export { TYPOGRAPHY, getFontSize } from './typography'
export { BREAKPOINTS, mediaQuery, matchesBreakpoint } from './breakpoints'

// Re-export as single object for convenience
import { SPACING } from './spacing'
import { LAYOUT } from './layout'
import { ANIMATION } from './animation'
import { TYPOGRAPHY } from './typography'
import { BREAKPOINTS } from './breakpoints'
import { normalizeFigmaTokens } from './figma'

export const DesignTokens = Object.freeze(normalizeFigmaTokens({
  SPACING,
  LAYOUT,
  ANIMATION,
  TYPOGRAPHY,
  BREAKPOINTS,
}))

export default DesignTokens
