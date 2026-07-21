/**
 * Branch Mode Rules (UX HINTS ONLY)
 *
 * S-Grade: Multi-output node rules for UI feedback.
 * Single source of truth: '@/services/nodeService'
 *
 * IMPORTANT: These rules are UX hints only, NOT authoritative.
 * The authoritative validation is done by the backend via POST /workflows/validate.
 * Frontend rules provide instant feedback but can be bypassed.
 */

import { nodeService } from '@/services/nodeService'

/**
 * Check if a node can have multiple outputs
 * @param {Object} node
 * @param {Object} modulesStore - Optional modules store
 * @returns {boolean}
 */
export function canHaveMultipleOutputs(node, modulesStore = null) {
  return nodeService.isMultiOutput(node.data?.module, modulesStore)
}

/**
 * Get maximum allowed outputs for a node
 * @param {Object} node
 * @param {Object} modulesStore - Optional modules store
 * @returns {number}
 */
export function getMaxOutputs(node, modulesStore = null) {
  const moduleId = node.data?.module || ''
  if (!canHaveMultipleOutputs(node, modulesStore)) return 1

  // Branch nodes (if/else): 2 outputs (true/false)
  if (nodeService.isBranch(moduleId, modulesStore)) return 2

  // Switch nodes: unlimited (dynamic cases)
  if (nodeService.isSwitch(moduleId, modulesStore)) return Infinity

  // Fork nodes: based on config
  if (nodeService.isFork(moduleId, modulesStore)) return Infinity

  return 2
}

/**
 * Check if node has reached max outputs
 * @param {string} nodeId
 * @param {Array} edges
 * @param {Object} node
 * @returns {boolean}
 */
export function hasReachedMaxOutputs(nodeId, edges, node) {
  // Exclude error edges — error outputs shouldn't count toward the max output limit
  const currentOutputs = edges.filter(e => e.source === nodeId && !e.sourceHandle?.includes('error')).length
  return currentOutputs >= getMaxOutputs(node)
}
