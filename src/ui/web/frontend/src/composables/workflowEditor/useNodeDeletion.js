/**
 * Node Deletion Composable
 *
 * Handles node and edge deletion, including reconnect/cascade dialogs,
 * orphaned switch case cleanup, and connection model updates.
 */

import { nextTick } from 'vue'
import { useModulesStore } from '@/stores/modulesStore'
import {
  createEdge,
  removeNodeWithCascade
} from './useCanvasOperations'
import { isLoopEdge, EDGE_PREFIXES } from './workflowConstants'
import { getNodeDeletionCascade, isLoopBackEdge } from './useNodeRules'
import { isLoopNode, isBranchNode, isSwitchNode } from '@/services/nodeService'
import { resolveModuleLabel } from '@/utils/moduleIdUtils'

import { createDeletionState, hasPathBetween } from './deletionState'

/**
 * @param {Object} options
 * @param {Ref<Array>} options.nodes - Nodes array
 * @param {Ref<Array>} options.edges - Edges array
 * @param {Function} options.onSync - Callback to sync to parent
 * @param {Function} options.onDelete - Callback when nodes deleted
 */
export function useNodeDeletion({ nodes, edges, onSync, onDelete }) {
  const modulesStore = useModulesStore()
  const delState = createDeletionState()

  /**
   * Clean orphaned cases from switch nodes based on specific removed edges.
   */
  function cleanOrphanedSwitchCases(removedEdges) {
    if (!removedEdges || removedEdges.length === 0) return
    const store = useModulesStore()

    const casesByNode = new Map()
    for (const edge of removedEdges) {
      if (!edge.sourceHandle?.startsWith('source-case-')) continue
      const caseId = edge.sourceHandle.replace('source-case-', '')
      const sourceNode = nodes.value.find(n => n.id === edge.source)
      if (!sourceNode) continue
      if (!isSwitchNode(sourceNode.data?.module || '', store)) continue
      if (!casesByNode.has(edge.source)) casesByNode.set(edge.source, new Set())
      casesByNode.get(edge.source).add(caseId)
    }

    for (const [nodeId, caseIds] of casesByNode) {
      const node = nodes.value.find(n => n.id === nodeId)
      if (!node?.data?.params?.cases) continue
      node.data.params.cases = node.data.params.cases.filter(c => {
        if (!caseIds.has(c.id)) return true
        const handleId = `source-case-${c.id}`
        return edges.value.some(e => e.source === nodeId && e.sourceHandle === handleId)
      })
    }
  }

  /**
   * Resolve the connection key for a given edge based on module type and handle
   */
  function resolveConnectionKey(moduleId, sourceHandle, edgeId, edgeToDelete) {
    const store = modulesStore

    if (isLoopNode(moduleId, store)) {
      if (sourceHandle === 'body_out' || sourceHandle.includes('item')) return 'iterate'
      if (sourceHandle === 'done_out' || sourceHandle.includes('done')) return 'done'
    }

    if (isBranchNode(moduleId, store)) {
      if (sourceHandle.includes('true') || edgeId.includes(EDGE_PREFIXES.BRANCH_TRUE)) return 'true'
      if (sourceHandle.includes('false') || edgeId.includes(EDGE_PREFIXES.BRANCH_FALSE)) return 'false'
    }

    if (isSwitchNode(moduleId, store)) {
      if (sourceHandle.includes('default') || edgeId.includes('default')) return 'default'
      if (sourceHandle.startsWith('source-case-') || sourceHandle === 'source-cases') {
        const edgeCaseId = edgeToDelete.data?.caseId || edgeToDelete.data?.caseKey
        const caseIdVal = sourceHandle.startsWith('source-case-')
          ? sourceHandle.replace('source-case-', '')
          : edgeCaseId
        return caseIdVal ? `case:${caseIdVal}` : null
      }
    }

    return null
  }

  /**
   * Update connections when edge is deleted (V1.2 Connections Model)
   */
  function updateConnectionsOnEdgeDelete(edgeToDelete, sourceId, targetId, remainingEdges = null) {
    const sourceNode = nodes.value.find(n => n.id === sourceId)
    if (!sourceNode?.data?.connections) return

    const connections = sourceNode.data.connections
    const moduleId = sourceNode.data?.module || ''
    const connectionKey = resolveConnectionKey(
      moduleId,
      edgeToDelete.sourceHandle || '',
      edgeToDelete.id || '',
      edgeToDelete
    )

    if (!connectionKey) return

    if (Array.isArray(connections[connectionKey])) {
      connections[connectionKey] = connections[connectionKey].filter(t => t !== targetId)
    }

    // Switch case cleanup: remove orphaned case when no edges remain
    if (connectionKey.startsWith('case:') && remainingEdges && sourceNode.data?.params?.cases) {
      const caseIdVal = connectionKey.replace('case:', '')
      const caseHandleId = `source-case-${caseIdVal}`
      const hasOtherEdges = remainingEdges.some(
        e => e.source === sourceId && e.sourceHandle === caseHandleId
      )
      if (!hasOtherEdges) {
        sourceNode.data.params.cases = sourceNode.data.params.cases.filter(c => c.id !== caseIdVal)
      }
    }
  }

  /**
   * Execute node deletion
   */
  async function executeDelete(nodeId, shouldReconnect, reconnectInfo = null) {
    const result = removeNodeWithCascade(nodes.value, edges.value, nodeId)

    const removedEdgeIds = new Set(result.edges.map(e => e.id))
    const removedEdges = edges.value.filter(e => !removedEdgeIds.has(e.id))

    nodes.value = result.nodes
    edges.value = result.edges

    cleanOrphanedSwitchCases(removedEdges)

    await nextTick()

    if (shouldReconnect && reconnectInfo) {
      const { sourceId, targetId } = reconnectInfo
      const sourceExists = nodes.value.some(n => n.id === sourceId)
      const targetExists = nodes.value.some(n => n.id === targetId)

      if (sourceExists && targetExists) {
        const newEdge = createEdge(sourceId, targetId)
        edges.value = [...edges.value, newEdge]
        await nextTick()
      }
    }

    onSync?.()
    onDelete?.({ deletedNodes: result.deletedNodes })
  }

  /**
   * Handle edge deletion
   */
  function handleDeleteEdge(edgeId) {
    const edgeToDelete = edges.value.find(e => e.id === edgeId)
    if (!edgeToDelete) return

    const sourceId = edgeToDelete.source
    const targetId = edgeToDelete.target

    const isBackEdge = hasPathBetween(targetId, sourceId, edges.value, edgeId)
    const edgesAfterRemoval = edges.value.filter(e => e.id !== edgeId)

    if (!isBackEdge) {
      const hasOtherIncoming = edgesAfterRemoval.some(e => e.target === targetId)
      const isWorkflowRoot = !edges.value.some(e => e.target === targetId)

      if (!hasOtherIncoming && !isWorkflowRoot) {
        const cascadeNodes = getNodeDeletionCascade(targetId, nodes.value, edgesAfterRemoval)
        const childCount = cascadeNodes.length

        if (childCount > 0) {
          delState.pendingDeleteEdgeId.value = edgeId
          delState.pendingDeleteEdgeInfo.value = {
            edgeId,
            sourceId,
            targetId,
            edgesAfterRemoval,
            cascadeNodes
          }
          delState.pendingDeleteChildCount.value = childCount
          delState.pendingDeleteChildrenInfo.value = {
            nodeId: targetId,
            incomingEdges: [{ source: sourceId }],
            outgoingEdges: edges.value.filter(e => e.source === targetId),
            cascadeNodes,
            isEdgeDeletion: true,
            edgeId
          }
          delState.showDeleteChildrenDialog.value = true
          return
        }
      }
    }

    updateConnectionsOnEdgeDelete(edgeToDelete, sourceId, targetId, edgesAfterRemoval)

    edges.value = edgesAfterRemoval
    onSync?.()
  }

  /**
   * Request node deletion (may show dialog)
   */
  function requestDeleteNode(nodeId) {
    const nodeToDelete = nodes.value.find(n => n.id === nodeId)
    if (!nodeToDelete) return

    if (isLoopNode(nodeToDelete.data?.module, modulesStore)) {
      executeDelete(nodeId, false)
      return
    }

    const incomingEdges = edges.value.filter(e => e.target === nodeId)
    const outgoingEdges = edges.value.filter(e => e.source === nodeId)
    const normalOutgoingEdges = outgoingEdges.filter(e => !isLoopBackEdge(e))

    if (normalOutgoingEdges.length > 0) {
      const cascadeNodes = getNodeDeletionCascade(nodeId, nodes.value, edges.value)
      const childCount = cascadeNodes.length - 1

      if (childCount > 0) {
        const nonLoopChildren = cascadeNodes.filter(id => {
          if (id === nodeId) return false
          const node = nodes.value.find(n => n.id === id)
          return node && !isLoopNode(node.data?.module, modulesStore)
        })

        if (nonLoopChildren.length === 0) {
          executeDelete(nodeId, false)
          return
        }

        delState.pendingDeleteChildCount.value = childCount
        delState.pendingDeleteChildrenInfo.value = {
          nodeId,
          incomingEdges,
          outgoingEdges: normalOutgoingEdges,
          cascadeNodes
        }
        delState.showDeleteChildrenDialog.value = true
        return
      }
    }

    if (incomingEdges.length === 1 && normalOutgoingEdges.length === 1) {
      const sourceNodeId = incomingEdges[0].source
      const targetNodeId = normalOutgoingEdges[0].target
      const targetNode = nodes.value.find(n => n.id === targetNodeId)

      if (sourceNodeId !== targetNodeId && targetNode && !isLoopNode(targetNode.data?.module, modulesStore)) {
        const sourceNode = nodes.value.find(n => n.id === sourceNodeId)

        delState.pendingDeleteNodeId.value = nodeId
        delState.pendingReconnectInfo.value = {
          sourceId: sourceNodeId,
          targetId: targetNodeId,
          sourceLabel: resolveModuleLabel(sourceNode?.data?.module, modulesStore) || sourceNodeId,
          targetLabel: resolveModuleLabel(targetNode?.data?.module, modulesStore) || targetNodeId
        }
        delState.showReconnectDialog.value = true
        return
      }
    }

    executeDelete(nodeId, false)
  }

  // Deletion dialog handlers

  function closeReconnectDialog() {
    delState.showReconnectDialog.value = false
    delState.pendingDeleteNodeId.value = null
    delState.pendingReconnectInfo.value = null
  }

  function closeDeleteChildrenDialog() {
    delState.showDeleteChildrenDialog.value = false
    delState.pendingDeleteChildCount.value = 0
    delState.pendingDeleteChildrenInfo.value = null
    delState.pendingDeleteEdgeId.value = null
    delState.pendingDeleteEdgeInfo.value = null
  }

  function confirmReconnect() {
    const nodeId = delState.pendingDeleteNodeId.value
    const reconnect = delState.pendingReconnectInfo.value
    executeDelete(nodeId, true, reconnect)
    closeReconnectDialog()
  }

  function skipReconnect() {
    const nodeId = delState.pendingDeleteNodeId.value
    executeDelete(nodeId, false)
    closeReconnectDialog()
  }

  function cancelDelete() {
    closeReconnectDialog()
  }

  async function handleMergeToChild() {
    const info = delState.pendingDeleteChildrenInfo.value
    if (!info) return

    const { nodeId, incomingEdges, outgoingEdges, edgeId } = info

    const removedEdges = edges.value.filter(e =>
      e.source === nodeId || e.target === nodeId || e.id === edgeId
    )

    nodes.value = nodes.value.filter(n => n.id !== nodeId)
    edges.value = edges.value.filter(e =>
      e.source !== nodeId && e.target !== nodeId && e.id !== edgeId
    )

    cleanOrphanedSwitchCases(removedEdges)

    await nextTick()

    const firstChildId = outgoingEdges[0]?.target
    if (incomingEdges.length > 0 && firstChildId) {
      const parentId = incomingEdges[0].source
      const parentExists = nodes.value.some(n => n.id === parentId)
      const childExists = nodes.value.some(n => n.id === firstChildId)

      if (parentExists && childExists) {
        const newEdge = createEdge(parentId, firstChildId)
        edges.value = [...edges.value, newEdge]
      }
    }

    await nextTick()
    closeDeleteChildrenDialog()
    onSync?.()
    onDelete?.({ deletedNodes: [nodeId] })
  }

  async function handleDeleteAllChildren() {
    const info = delState.pendingDeleteChildrenInfo.value
    if (!info) return

    const { cascadeNodes, edgeId } = info

    const removedEdges = edges.value.filter(e =>
      cascadeNodes.includes(e.source) ||
      cascadeNodes.includes(e.target) ||
      e.id === edgeId
    )

    nodes.value = nodes.value.filter(n => !cascadeNodes.includes(n.id))
    edges.value = edges.value.filter(e =>
      !cascadeNodes.includes(e.source) &&
      !cascadeNodes.includes(e.target) &&
      e.id !== edgeId
    )

    cleanOrphanedSwitchCases(removedEdges)

    await nextTick()
    closeDeleteChildrenDialog()
    onSync?.()
    onDelete?.({ deletedNodes: cascadeNodes })
  }

  function cancelDeleteWithChildren() {
    closeDeleteChildrenDialog()
  }

  return {
    // Deletion dialog state
    showReconnectDialog: delState.showReconnectDialog,
    pendingDeleteNodeId: delState.pendingDeleteNodeId,
    pendingReconnectInfo: delState.pendingReconnectInfo,
    reconnectDialogTitle: delState.reconnectDialogTitle,
    reconnectDialogMessage: delState.reconnectDialogMessage,
    showDeleteChildrenDialog: delState.showDeleteChildrenDialog,
    pendingDeleteChildCount: delState.pendingDeleteChildCount,
    pendingDeleteChildrenInfo: delState.pendingDeleteChildrenInfo,

    // Deletion methods
    hasPathBetween,
    handleDeleteEdge,
    requestDeleteNode,
    confirmReconnect,
    skipReconnect,
    cancelDelete,
    handleMergeToChild,
    handleDeleteAllChildren,
    cancelDeleteWithChildren
  }
}
