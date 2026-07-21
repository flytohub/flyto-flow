/**
 * Loop Mode Rules (UX HINTS ONLY)
 *
 * S-Grade: Loop node detection and rules for UI feedback.
 * Type checks: Use '@/services/nodeService'
 *
 * IMPORTANT: These rules are UX hints only, NOT authoritative.
 * The authoritative validation is done by the backend via POST /workflows/validate.
 * Frontend rules provide instant feedback but can be bypassed.
 */

import { isLoopEdge } from '../workflowConstants'
import { nodeService } from '@/services/nodeService'
import { useModulesStore } from '@/stores/modulesStore'

/**
 * Check if workflow has any loop-type nodes
 * @param {Array} nodes
 * @param {object} modulesStore - Optional modules store
 * @returns {boolean}
 */
export function hasLoopNodes(nodes, modulesStore = null) {
  const store = modulesStore || useModulesStore()
  return nodes.some(node => nodeService.isLoop(node.data?.module, store))
}

/**
 * Check if workflow has any active loop edges (back-edges)
 * @param {Array} edges
 * @returns {boolean}
 */
export function hasLoopEdges(edges) {
  return edges.some(edge => isLoopEdge(edge))
}

/**
 * Check if a specific node is a loop-type node
 * @param {Object} node
 * @param {object} modulesStore - Optional modules store
 * @returns {boolean}
 */
export function isLoopNode(node, modulesStore = null) {
  const store = modulesStore || useModulesStore()
  return nodeService.isLoop(node.data?.module, store)
}

// Re-export for convenience
export { isLoopNode as isLoopModule } from '@/services/nodeService'
