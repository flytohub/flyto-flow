/**
 * Node Utilities
 *
 * S-Grade: Single responsibility - node creation and utilities only.
 * Type checks: Use '@/services/nodeService' directly
 */

import { getRandomSuffix } from '../workflowConstants'
import { nodeService } from '@/services/nodeService'
import { useModulesStore } from '@/stores/modulesStore'

// Counter for ensuring unique IDs within the same millisecond
let nodeIdCounter = 0

/**
 * Create a new node object
 */
export function createNode({ id, type = 'default', position, label, data = {} }) {
  return {
    id,
    type,
    position,
    label,
    data
  }
}

/**
 * Generate unique node ID
 * Uses timestamp + counter + random suffix to prevent collisions
 */
export function generateNodeId() {
  const uniqueSuffix = `${Date.now()}_${nodeIdCounter++}_${getRandomSuffix()}`
  return `node_${uniqueSuffix}`
}

/**
 * Calculate position for new node relative to source
 */
export function calculateNewNodePosition(sourceNode, offsetX = 280, offsetY = 0) {
  return {
    x: (sourceNode.position?.x || 200) + offsetX,
    y: (sourceNode.position?.y || 100) + offsetY
  }
}

/**
 * Filter nodes from elements array
 */
export function filterNodes(elements) {
  if (!elements || !Array.isArray(elements)) return []
  return elements.filter(el => el && !el.source)
}

/**
 * Get node type category from module ID
 */
export function getNodeCategory(moduleId) {
  if (!moduleId) return 'default'
  return moduleId.split('.')[0]
}

/**
 * Check if node is a flow control node
 * @param {string} moduleId - Module identifier
 * @param {object} modulesStore - Optional modules store
 */
export function isFlowControlNode(moduleId, modulesStore = null) {
  if (!moduleId) return false
  const store = modulesStore || useModulesStore()
  return nodeService.isFlowControl(moduleId, store)
}

/**
 * Check if node is a loop/goto node (connects back, no add button needed)
 * @param {string} moduleId - Module identifier
 * @param {object} modulesStore - Optional modules store
 */
export function isLoopOrGotoNode(moduleId, modulesStore = null) {
  if (!moduleId) return false
  const store = modulesStore || useModulesStore()
  return nodeService.isLoop(moduleId, store)
}
