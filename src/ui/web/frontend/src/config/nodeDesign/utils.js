/**
 * Node Design System — Utility Functions
 * All helper/utility functions
 */

import { NODE, HANDLE, BUTTON } from './dimensions.js'
import { COLORS } from './colors.js'
import { SHAPE_EFFECTS } from './animations.js'
import { LAYOUT } from './layout.js'

// =============================================================================
// LAYOUT HELPER FUNCTIONS
// =============================================================================

/**
 * Calculate next node X position based on edge-to-edge spacing
 * @param {number} currentX - Current node X position
 * @param {string} currentShape - Current node shape name
 * @returns {number} Next node X position
 */
export function getNextNodeX(currentX, currentShape) {
  const currentWidth = NODE.shapes[currentShape]?.width || NODE.width
  return currentX + currentWidth + LAYOUT.spacing.horizontal
}

/**
 * Calculate centered Y positions for multi-output children
 * @param {number} parentY - Parent node Y position
 * @param {number} childCount - Number of children
 * @param {number} spacing - Vertical spacing between children
 * @returns {number[]} Array of Y positions for each child
 */
export function getCenteredChildPositions(parentY, childCount, spacing = LAYOUT.spacing.caseSpacing) {
  if (childCount === 0) return []
  if (childCount === 1) return [parentY]

  const totalHeight = (childCount - 1) * spacing
  const startY = parentY - totalHeight / 2

  return Array.from({ length: childCount }, (_, i) => startY + i * spacing)
}

/**
 * Get node connection point (handle position in canvas coordinates)
 * @param {object} node - Node object with position and shape
 * @param {string} handlePosition - 'left' | 'right' | 'top' | 'bottom'
 * @returns {object} { x, y } canvas coordinates
 */
export function getHandleCanvasPosition(node, handlePosition) {
  const shape = NODE.shapes[node.shape] || NODE.shapes.rectangle
  const nodeX = node.position?.x || 0
  const nodeY = node.position?.y || 0

  switch (handlePosition) {
    case 'left':
      return { x: nodeX, y: nodeY + shape.height / 2 }
    case 'right':
      return { x: nodeX + shape.width, y: nodeY + shape.height / 2 }
    case 'top':
      return { x: nodeX + shape.width / 2, y: nodeY }
    case 'bottom':
      return { x: nodeX + shape.width / 2, y: nodeY + shape.height }
    default:
      return { x: nodeX + shape.width / 2, y: nodeY + shape.height / 2 }
  }
}

/**
 * Calculate edge path avoiding overlaps
 * @param {object} source - Source handle position { x, y }
 * @param {object} target - Target handle position { x, y }
 * @param {string} type - Edge type
 * @returns {string} SVG path string
 */
export function calculateEdgePath(source, target, type = 'smoothstep') {
  const dx = target.x - source.x
  const dy = target.y - source.y

  if (type === 'straight') {
    return `M ${source.x} ${source.y} L ${target.x} ${target.y}`
  }

  // Smoothstep: horizontal, then vertical, then horizontal
  const midX = source.x + dx / 2
  const radius = Math.min(LAYOUT.connection.borderRadius, Math.abs(dx) / 4, Math.abs(dy) / 4)

  return `M ${source.x} ${source.y}
          L ${midX - radius} ${source.y}
          Q ${midX} ${source.y} ${midX} ${source.y + (dy > 0 ? radius : -radius)}
          L ${midX} ${target.y - (dy > 0 ? radius : -radius)}
          Q ${midX} ${target.y} ${midX + radius} ${target.y}
          L ${target.x} ${target.y}`
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Generate button gradient from color
 */
export function getButtonGradient(color) {
  return `linear-gradient(135deg, ${color} 0%, ${color}aa 100%)`
}

/**
 * Get shape configuration
 */
export function getShapeConfig(shapeName) {
  return NODE.shapes[shapeName] || NODE.shapes.rectangle
}

/**
 * Calculate precise handle position (aligned with shape vertex/edge)
 * @param {string} shapeName - Shape name
 * @param {string} position - 'left' | 'right' | 'top' | 'bottom'
 * @param {string} color - Handle color type
 * @returns {object} CSS style object
 */
export function getHandlePosition(shapeName, position, color = 'default') {
  const shape = getShapeConfig(shapeName)
  const handleSize = HANDLE.size
  const offset = shape.handleOffset || -6

  const baseStyle = {
    width: `${handleSize}px`,
    height: `${handleSize}px`,
    border: `${HANDLE.borderWidth}px solid ${HANDLE.borderColors[color] || HANDLE.borderColor}`,
    background: HANDLE.colors[color] || HANDLE.colors.default,
    borderRadius: '50%',
    transition: HANDLE.transition,
    position: 'absolute'
  }

  switch (position) {
    case 'left':
      return {
        ...baseStyle,
        left: `${offset}px`,
        top: '50%',
        transform: 'translateY(-50%)'
      }
    case 'right':
      return {
        ...baseStyle,
        right: `${-offset}px`,
        top: '50%',
        transform: 'translateY(-50%)'
      }
    case 'top':
      return {
        ...baseStyle,
        top: `${offset}px`,
        left: '50%',
        transform: 'translateX(-50%)'
      }
    case 'bottom':
      return {
        ...baseStyle,
        bottom: `${-offset}px`,
        left: '50%',
        transform: 'translateX(-50%)'
      }
    default:
      return baseStyle
  }
}

/**
 * Generate handle style (legacy compatibility)
 */
export function getHandleStyle(position, color = 'default') {
  return getHandlePosition('rectangle', position, color)
}

/**
 * Get diamond inner shape style
 * Ensures rotated vertices align with container edges
 */
export function getDiamondInnerStyle() {
  const config = NODE.shapes.diamond
  return {
    width: `${config.innerSize}px`,
    height: `${config.innerSize}px`,
    borderRadius: `${config.innerBorderRadius}px`,
    transform: config.transform,
    position: 'absolute',
    top: '50%',
    left: '50%',
    marginTop: `-${config.innerSize / 2}px`,
    marginLeft: `-${config.innerSize / 2}px`
  }
}

/**
 * Get shape effect configuration
 */
export function getShapeEffect(shapeName) {
  return SHAPE_EFFECTS[shapeName] || SHAPE_EFFECTS.rectangle
}

/**
 * Generate selected state border effect CSS
 * Works with any shape by using the correct border-radius/clip-path
 * @param {string} shapeName - Shape name
 * @param {string} gradientColors - Gradient colors (default: purple-cyan-pink)
 * @returns {object} CSS for ::before pseudo-element
 */
export function getSelectedEffectStyle(shapeName, gradientColors = '#8B5CF6, #06B6D4, #EC4899, #8B5CF6') {
  const effect = getShapeEffect(shapeName)

  const base = {
    content: '""',
    position: 'absolute',
    inset: '-2px',
    padding: '2px',
    background: `linear-gradient(90deg, ${gradientColors})`,
    backgroundSize: '300% 100%',
    animation: 'border-flow 3s linear infinite',
    WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
    WebkitMaskComposite: 'xor',
    maskComposite: 'exclude',
    pointerEvents: 'none'
  }

  if (effect.maskType === 'clip-path') {
    return {
      ...base,
      clipPath: effect.outerClipPath || effect.clipPath
    }
  }

  if (effect.maskType === 'diamond') {
    return {
      ...base,
      width: `${effect.innerSize + 4}px`,
      height: `${effect.innerSize + 4}px`,
      borderRadius: effect.outerRadius,
      transform: effect.transform,
      top: '50%',
      left: '50%',
      marginTop: `-${(effect.innerSize + 4) / 2}px`,
      marginLeft: `-${(effect.innerSize + 4) / 2}px`,
      inset: 'auto'
    }
  }

  return {
    ...base,
    borderRadius: effect.outerRadius
  }
}

/**
 * Generate running/pulse effect CSS
 * @param {string} shapeName - Shape name
 * @param {string} color - Pulse color (rgba format)
 * @returns {object} CSS style object
 */
export function getRunningEffectStyle(shapeName, color = 'rgba(139, 92, 246, 0.4)') {
  const effect = getShapeEffect(shapeName)

  // Box-shadow works for all shapes with border-radius
  // For clip-path shapes, we use filter: drop-shadow instead
  if (effect.maskType === 'clip-path') {
    return {
      animation: 'running-pulse-filter 1.5s ease-in-out infinite',
      filter: `drop-shadow(0 0 4px ${color})`
    }
  }

  return {
    animation: 'running-pulse 1.5s ease-in-out infinite',
    '--pulse-color': color
  }
}

/**
 * Generate checkpoint ripple effect CSS
 * @param {string} shapeName - Shape name
 * @param {string} color - Ripple color
 * @returns {object} CSS for ::before and ::after pseudo-elements
 */
export function getCheckpointEffectStyle(shapeName, color = '#EF4444') {
  const effect = getShapeEffect(shapeName)

  const baseRipple = {
    content: '""',
    position: 'absolute',
    inset: '-2px',
    border: `2px solid ${color}`,
    pointerEvents: 'none',
    animation: 'ripple-ring 2.5s ease-out infinite'
  }

  if (effect.maskType === 'clip-path') {
    return {
      before: {
        ...baseRipple,
        clipPath: effect.clipPath
      },
      after: {
        ...baseRipple,
        clipPath: effect.clipPath,
        animationDelay: '0.8s'
      }
    }
  }

  if (effect.maskType === 'diamond') {
    const size = effect.innerSize + 4
    return {
      before: {
        ...baseRipple,
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: effect.outerRadius,
        transform: effect.transform,
        top: '50%',
        left: '50%',
        marginTop: `-${size / 2}px`,
        marginLeft: `-${size / 2}px`,
        inset: 'auto'
      },
      after: {
        ...baseRipple,
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: effect.outerRadius,
        transform: effect.transform,
        top: '50%',
        left: '50%',
        marginTop: `-${size / 2}px`,
        marginLeft: `-${size / 2}px`,
        inset: 'auto',
        animationDelay: '0.8s'
      }
    }
  }

  return {
    before: {
      ...baseRipple,
      borderRadius: effect.outerRadius
    },
    after: {
      ...baseRipple,
      borderRadius: effect.outerRadius,
      animationDelay: '0.8s'
    }
  }
}

/**
 * Generate all effect CSS variables for a shape
 * Use this to set CSS custom properties on a node
 */
export function getShapeEffectVars(shapeName) {
  const effect = getShapeEffect(shapeName)
  return {
    '--shape-border-radius': effect.borderRadius || 'none',
    '--shape-outer-radius': effect.outerRadius || 'none',
    '--shape-clip-path': effect.clipPath || 'none',
    '--shape-mask-type': effect.maskType
  }
}

/**
 * Generate delete button style
 */
export function getDeleteButtonStyle(size = 'default') {
  const sizeValue = size === 'small' ? BUTTON.delete.sizeSmall :
                    size === 'medium' ? BUTTON.delete.sizeMedium :
                    BUTTON.delete.size
  return {
    width: `${sizeValue}px`,
    height: `${sizeValue}px`,
    borderRadius: BUTTON.delete.borderRadius,
    border: `${BUTTON.delete.borderWidth}px solid ${BUTTON.delete.borderColor}`,
    background: BUTTON.delete.background,
    color: BUTTON.delete.color,
    zIndex: BUTTON.delete.zIndex,
    opacity: BUTTON.delete.opacity,
    transition: BUTTON.delete.transition,
    ...BUTTON.delete.position
  }
}

/**
 * Generate node container style
 */
export function getNodeContainerStyle(shapeName) {
  const shape = getShapeConfig(shapeName)
  return {
    position: 'relative',
    width: `${shape.width}px`,
    height: `${shape.height}px`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  }
}

/**
 * Generate shape visual style (actual shape inside container)
 */
export function getShapeVisualStyle(shapeName, borderColor = COLORS.border.default) {
  const shape = getShapeConfig(shapeName)

  const base = {
    background: NODE.card.background,
    border: `${NODE.card.borderWidth}px solid ${borderColor}`,
    boxShadow: NODE.card.shadow,
    transition: NODE.card.transition
  }

  if (shapeName === 'diamond') {
    return {
      ...base,
      ...getDiamondInnerStyle()
    }
  }

  if (shapeName === 'hexagon') {
    return {
      ...base,
      width: '100%',
      height: '100%',
      clipPath: shape.clipPath
    }
  }

  return {
    ...base,
    width: '100%',
    height: '100%',
    borderRadius: typeof shape.borderRadius === 'number'
      ? `${shape.borderRadius}px`
      : shape.borderRadius
  }
}
