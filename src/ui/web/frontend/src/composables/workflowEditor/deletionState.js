/**
 * Deletion State — Node/edge deletion state and graph traversal
 *
 * Manages reactive state for deletion dialogs (reconnect, cascade)
 * and provides the hasPathBetween graph traversal utility.
 */

import { ref, computed } from 'vue'

/**
 * Creates the deletion dialog state subsystem.
 *
 * @returns {Object} Deletion state refs and computed properties
 */
export function createDeletionState() {
  const showReconnectDialog = ref(false)
  const pendingDeleteNodeId = ref(null)
  const pendingReconnectInfo = ref(null)

  const showDeleteChildrenDialog = ref(false)
  const pendingDeleteChildCount = ref(0)
  const pendingDeleteChildrenInfo = ref(null)

  const pendingDeleteEdgeId = ref(null)
  const pendingDeleteEdgeInfo = ref(null)

  const reconnectDialogTitle = computed(() => 'Reconnect Nodes?')
  const reconnectDialogMessage = computed(() => {
    if (!pendingReconnectInfo.value) return ''
    const { sourceLabel, targetLabel } = pendingReconnectInfo.value
    return `Do you want to connect "${sourceLabel}" to "${targetLabel}" after deletion?`
  })

  return {
    showReconnectDialog,
    pendingDeleteNodeId,
    pendingReconnectInfo,
    showDeleteChildrenDialog,
    pendingDeleteChildCount,
    pendingDeleteChildrenInfo,
    pendingDeleteEdgeId,
    pendingDeleteEdgeInfo,
    reconnectDialogTitle,
    reconnectDialogMessage
  }
}

/**
 * Check if path exists between nodes (BFS)
 */
export function hasPathBetween(fromId, toId, allEdges, excludeEdgeId) {
  const visited = new Set()
  const queue = [fromId]

  while (queue.length > 0) {
    const current = queue.shift()
    if (current === toId) return true
    if (visited.has(current)) continue
    visited.add(current)

    const outgoing = allEdges.filter(e => e.source === current && e.id !== excludeEdgeId)
    for (const edge of outgoing) {
      queue.push(edge.target)
    }
  }

  return false
}
