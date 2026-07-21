/**
 * Node Helpers — Pure utility functions for node operations
 *
 * Parameter initialization, coordinate calculation helpers.
 * All functions are pure (or depend only on stores) and independently testable.
 */

import { useModulesStore } from '@/stores/modulesStore'
import { calculateNewNodePosition } from './useCanvasOperations'

// ============================================================================
// Parameter initialization
// ============================================================================

/**
 * Unified parameter initialization.
 * Backend is single source of truth — uses pre-computed defaultParams.
 * Priority: overrides > backend defaultParams > module.params
 */
export function initializeParams(moduleId, module = {}, overrides = {}) {
  const modulesStore = useModulesStore()
  const metadata = modulesStore.modulesMetadata?.[moduleId]
  const defaults = metadata?.defaultParams || module.defaultParams || {}
  const merged = {
    ...defaults,
    ...(module.params || {}),
    ...overrides
  }
  // Deep clone to prevent shared references between nodes
  try { return JSON.parse(JSON.stringify(merged)) } catch { return { ...merged } }
}

// ============================================================================
// Position calculation
// ============================================================================

/**
 * Calculate midpoint between two nodes for edge insertion
 */
export function calculateEdgeMidpoint(sourceNode, targetNode) {
  const sourceWidth = sourceNode.dimensions?.width || sourceNode.width || 200
  const sourceHeight = sourceNode.dimensions?.height || sourceNode.height || 80
  const targetWidth = targetNode.dimensions?.width || targetNode.width || 200

  const sourceX = sourceNode.position.x + sourceWidth / 2
  const sourceY = sourceNode.position.y + sourceHeight
  const targetX = targetNode.position.x + targetWidth / 2
  const targetY = targetNode.position.y

  const newNodeWidth = 200
  return {
    x: (sourceX + targetX) / 2 - newNodeWidth / 2,
    y: (sourceY + targetY) / 2
  }
}

/**
 * Calculate position for multi-output node connections
 */
export function calculateMultiOutputPosition(parentNode, handle, caseId, edges) {
  const cases = parentNode.data?.params?.cases || []
  const edgesFromHandle = edges.value.filter(e =>
    e.source === parentNode.id && e.sourceHandle === handle
  )
  const stackOffset = edgesFromHandle.length * 120

  if (handle === 'source-cases' || handle.startsWith('source-case-')) {
    const caseIndex = caseId
      ? cases.findIndex(c => c.id === caseId)
      : 0
    return {
      x: parentNode.position.x + 280 + stackOffset,
      y: parentNode.position.y + (Math.max(0, caseIndex) * 100)
    }
  } else if (handle === 'source-default') {
    return {
      x: parentNode.position.x,
      y: parentNode.position.y + 180 + stackOffset
    }
  } else if (handle === 'source-true') {
    return {
      x: parentNode.position.x + 280 + stackOffset,
      y: parentNode.position.y
    }
  } else if (handle === 'source-false') {
    return {
      x: parentNode.position.x,
      y: parentNode.position.y + 180 + stackOffset
    }
  } else if (handle === 'body_out') {
    return {
      x: parentNode.position.x,
      y: parentNode.position.y + 180 + stackOffset
    }
  } else if (handle === 'done_out') {
    return {
      x: parentNode.position.x + 280 + stackOffset,
      y: parentNode.position.y
    }
  }

  return calculateNewNodePosition(parentNode)
}

/**
 * Calculate a smart default position for standalone nodes
 */
export function calculateStandalonePosition(nodes) {
  if (nodes.value.length === 0) {
    return { x: 250, y: 150 }
  }
  const maxX = Math.max(...nodes.value.map(n => n.position.x))
  const maxY = Math.max(...nodes.value.map(n => n.position.y))
  return { x: maxX + 200, y: maxY }
}
