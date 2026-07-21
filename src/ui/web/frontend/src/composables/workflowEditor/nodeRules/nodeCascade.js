/**
 * Node Cascade Rules
 *
 * S-Grade: Node deletion cascade logic.
 * Single source of truth: '@/services/nodeService'
 */

import { isLoopEdge } from '../workflowConstants'
import { nodeService } from '@/services/nodeService'
import { useModulesStore } from '@/stores/modulesStore'

/**
 * Check if an edge is a loop-back edge (points backward in the flow)
 * @param {Object} edge
 * @returns {boolean}
 */
export function isLoopBackEdge(edge) {
  return isLoopEdge(edge)
}

/**
 * Get all descendant node IDs that should be deleted when parent is deleted
 * @param {string} parentId - The node being deleted
 * @param {Array} nodes - All nodes
 * @param {Array} edges - All edges
 * @param {object} modulesStore - Optional modules store
 * @returns {Array<string>} Array of node IDs to delete (includes parentId)
 */
export function getNodeDeletionCascade(parentId, nodes, edges, modulesStore = null) {
  const store = modulesStore || useModulesStore()
  const toDelete = new Set([parentId])
  const queue = [parentId]

  while (queue.length > 0) {
    const currentId = queue.shift()

    // Find all direct children (nodes that have this node as source)
    // Include ALL outgoing edges, not just forward ones
    const childEdges = edges.filter(e => e.source === currentId)

    for (const edge of childEdges) {
      const childId = edge.target
      const childNode = nodes.find(n => n.id === childId)

      // Special case: Loop nodes should always be deleted with their parent
      // because they depend on the flow structure
      if (childNode && nodeService.isLoop(childNode.data?.module, store)) {
        if (!toDelete.has(childId)) {
          toDelete.add(childId)
          // Don't queue loop nodes - they don't have meaningful children
          // (their "children" via loop-back edges are actually ancestors)
        }
        continue
      }

      // For non-loop nodes: check if child has other parents
      // Exclude loop-back edges when counting parents (they're not real dependencies)
      const otherParents = edges.filter(e => {
        if (e.target !== childId) return false
        if (toDelete.has(e.source)) return false
        // Don't count loop-back edges as parent connections
        if (isLoopBackEdge(e)) return false
        return true
      })

      // Only delete child if it has no other (non-loop) parents
      if (otherParents.length === 0 && !toDelete.has(childId)) {
        toDelete.add(childId)
        queue.push(childId)
      }
    }

    // Also find resource sub-nodes that point TO this node
    // Resource edges: source = sub-node, target = AI Agent
    const resourceInEdges = edges.filter(e => {
      if (e.target !== currentId) return false
      const th = e.targetHandle || ''
      if (/^target-(model|memory|tools)/.test(th)) return true
      const dt = (e.data?.edgeType || '').toLowerCase()
      return dt === 'resource'
    })

    for (const edge of resourceInEdges) {
      const subNodeId = edge.source
      if (!toDelete.has(subNodeId)) {
        toDelete.add(subNodeId)
        // Don't queue — sub-nodes have no further children
      }
    }
  }

  return Array.from(toDelete)
}

/**
 * Get edges to remove when nodes are deleted
 * @param {Array<string>} nodeIds - Node IDs being deleted
 * @param {Array} edges - All edges
 * @returns {Array} Edges to keep
 */
export function getEdgesAfterNodeDeletion(nodeIds, edges) {
  const deleteSet = new Set(nodeIds)
  return edges.filter(
    edge => !deleteSet.has(edge.source) && !deleteSet.has(edge.target)
  )
}
