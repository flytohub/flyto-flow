/**
 * Node Design System — Backward Compatibility Re-export
 *
 * This file re-exports everything from '@/config/nodeDesign' so that
 * existing imports like:
 *   import { NODE, LAYOUT } from '@/config/nodeDesignSystem'
 * continue to work without changes.
 *
 * For new code, prefer importing from '@/config/nodeDesign' directly.
 */

export {
  // Config objects
  NODE,
  HANDLE,
  BUTTON,
  BADGE,
  COLORS,
  GRADIENTS,
  STATES,
  ANIMATIONS,
  SHAPE_EFFECTS,
  TRANSITIONS,
  LAYOUT,
  Z_INDEX,
  // Utility functions
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
} from './nodeDesign/index.js'

export { default } from './nodeDesign/index.js'
