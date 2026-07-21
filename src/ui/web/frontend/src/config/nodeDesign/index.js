/**
 * Node Design System
 * All node components must follow these specifications.
 *
 * Purpose: Unified node visual style, ensure consistency, easy maintenance
 *
 * Usage:
 * import { NODE, HANDLE, BUTTON, COLORS, ANIMATIONS } from '@/config/nodeDesign'
 */

// Config objects
export { NODE, HANDLE, BUTTON, BADGE } from './dimensions.js'
export { COLORS, GRADIENTS, STATES } from './colors.js'
export { ANIMATIONS, SHAPE_EFFECTS, TRANSITIONS } from './animations.js'
export { LAYOUT, Z_INDEX } from './layout.js'

// Utility functions
export {
  getNextNodeX,
  getCenteredChildPositions,
  getHandleCanvasPosition,
  calculateEdgePath,
  getButtonGradient,
  getShapeConfig,
  getHandlePosition,
  getHandleStyle,
  getDiamondInnerStyle,
  getShapeEffect,
  getSelectedEffectStyle,
  getRunningEffectStyle,
  getCheckpointEffectStyle,
  getShapeEffectVars,
  getDeleteButtonStyle,
  getNodeContainerStyle,
  getShapeVisualStyle
} from './utils.js'

// Default export for backward compatibility
import { NODE, HANDLE, BUTTON, BADGE } from './dimensions.js'
import { COLORS, GRADIENTS, STATES } from './colors.js'
import { ANIMATIONS, SHAPE_EFFECTS, TRANSITIONS } from './animations.js'
import { LAYOUT, Z_INDEX } from './layout.js'
import {
  getButtonGradient,
  getShapeConfig,
  getHandlePosition,
  getHandleStyle,
  getDiamondInnerStyle,
  getDeleteButtonStyle,
  getNodeContainerStyle,
  getShapeVisualStyle,
  getShapeEffect,
  getSelectedEffectStyle,
  getRunningEffectStyle,
  getCheckpointEffectStyle,
  getShapeEffectVars,
  getNextNodeX,
  getCenteredChildPositions,
  getHandleCanvasPosition,
  calculateEdgePath
} from './utils.js'

export default {
  NODE,
  HANDLE,
  BUTTON,
  COLORS,
  GRADIENTS,
  ANIMATIONS,
  STATES,
  BADGE,
  Z_INDEX,
  TRANSITIONS,
  LAYOUT,
  SHAPE_EFFECTS,
  // Helper functions
  getButtonGradient,
  getShapeConfig,
  getHandlePosition,
  getHandleStyle,
  getDiamondInnerStyle,
  getDeleteButtonStyle,
  getNodeContainerStyle,
  getShapeVisualStyle,
  // Effect functions
  getShapeEffect,
  getSelectedEffectStyle,
  getRunningEffectStyle,
  getCheckpointEffectStyle,
  getShapeEffectVars,
  // Layout functions
  getNextNodeX,
  getCenteredChildPositions,
  getHandleCanvasPosition,
  calculateEdgePath
}
