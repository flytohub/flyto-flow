/**
 * Cascade Delete Utilities
 *
 * S-Grade: Single responsibility - node deletion with cascade logic.
 */

import { getNodeDeletionCascade, getEdgesAfterNodeDeletion } from '../useNodeRules'

/**
 * Remove node and its connected edges (simple version)
 */
export function removeNodeWithEdges(nodes, edges, nodeId) {
  const filteredNodes = nodes.filter(n => n.id !== nodeId)
  const filteredEdges = edges.filter(e => e.source !== nodeId && e.target !== nodeId)
  return { nodes: filteredNodes, edges: filteredEdges }
}

/**
 * Remove node with cascade delete of orphaned children
 */
export function removeNodeWithCascade(nodes, edges, nodeId) {
  const nodeIdsToDelete = getNodeDeletionCascade(nodeId, nodes, edges)
  const filteredNodes = nodes.filter(n => !nodeIdsToDelete.includes(n.id))
  const filteredEdges = getEdgesAfterNodeDeletion(nodeIdsToDelete, edges)

  return {
    nodes: filteredNodes,
    edges: filteredEdges,
    deletedNodes: nodeIdsToDelete
  }
}
