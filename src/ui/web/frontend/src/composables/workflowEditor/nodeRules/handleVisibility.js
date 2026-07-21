/**
 * Handle Visibility Rules
 *
 * S-Grade: Node handle visibility logic.
 * Single responsibility: Determine which handles to show.
 */

/**
 * Determine which handles should be visible for a node
 * @param {Object} options
 * @param {string} options.nodeId - Current node ID
 * @param {Array} options.edges - All edges in the workflow
 * @param {boolean} options.isFirstNode - Is this the first node in workflow
 * @param {boolean} options.loopModeEnabled - Is loop mode enabled in workflow
 * @param {string} options.nodeType - Node type (e.g., 'loop', 'condition', 'normal')
 * @returns {Object} { showTarget: boolean, showSource: boolean, showTopHandle: boolean, showBottomHandle: boolean }
 */
export function getHandleVisibility({
  nodeId,
  edges = [],
  isFirstNode = false,
  loopModeEnabled = false,
  nodeType = 'normal'
}) {
  // Default: show source (right), conditionally show target (left)
  const result = {
    showTarget: true,      // Left handle (input)
    showSource: true,      // Right handle (output)
    showTopHandle: false,  // Top handle (for loops)
    showBottomHandle: false // Bottom handle (for loops)
  }

  // Rule 1: First node has no target (left) handle unless loop mode
  if (isFirstNode && !loopModeEnabled) {
    result.showTarget = false
  }

  // Rule 2: Loop mode enables additional handles
  if (loopModeEnabled) {
    // First node gets target back (for loop return)
    if (isFirstNode) {
      result.showTarget = true
    }
    // Loop nodes get top/bottom handles
    if (nodeType === 'loop' || nodeType === 'agent') {
      result.showTopHandle = true
      result.showBottomHandle = true
    }
  }

  return result
}

/**
 * Check if a node is the first node (no incoming control-flow edges)
 * Excludes resource edges (Model/Memory/Tools → AI Agent) which use
 * targetHandle like 'target-model', 'target-memory', 'target-tools'.
 * @param {string} nodeId
 * @param {Array} edges
 * @returns {boolean}
 */
export function isFirstNode(nodeId, edges = []) {
  return !edges.some(edge => {
    if (edge.target !== nodeId) return false
    // Resource edges don't count as incoming control-flow
    const th = edge.targetHandle || ''
    if (/^target-(model|memory|tools)/.test(th)) return false
    const dt = (edge.data?.edgeType || '').toLowerCase()
    if (dt === 'resource') return false
    return true
  })
}

/**
 * Check if a node is a leaf node (no outgoing edges)
 * @param {string} nodeId
 * @param {Array} edges
 * @returns {boolean}
 */
export function isLeafNode(nodeId, edges = []) {
  return !edges.some(edge => edge.source === nodeId)
}
