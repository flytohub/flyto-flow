/**
 * Workflow Clipboard Composable
 *
 * Enables cross-workflow copy/paste for nodes and edges.
 * Uses the browser Clipboard API to support copy/paste between browser windows.
 *
 * Features:
 * - Copy selected nodes with their configurations
 * - Copy connected edges between selected nodes
 * - Paste nodes with new IDs at offset position
 * - Preserve node data and params
 */

import { ref } from 'vue'
import { generateNodeId } from './useCanvasOperations'

// Clipboard data marker to identify flyto workflow data
const CLIPBOARD_MARKER = 'flyto-workflow-v1'

/**
 * Create clipboard composable
 * @param {Object} options
 * @param {Ref<Array>} options.nodes - Nodes array
 * @param {Ref<Array>} options.edges - Edges array
 * @param {Function} options.onSync - Callback to sync changes to parent
 * @param {Function} options.onBeforePaste - Callback before pasting (for history)
 */
export function useClipboard({ nodes, edges, onSync, onBeforePaste }) {
  const isCopying = ref(false)
  const isPasting = ref(false)
  const lastPastePosition = ref({ x: 0, y: 0 })

  /**
   * Deep clone an object
   */
  function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj))
  }

  /**
   * Get selected nodes
   */
  function getSelectedNodes() {
    return nodes.value.filter(n => n.selected)
  }

  /**
   * Get edges connected between the given node IDs
   */
  function getConnectedEdges(nodeIds) {
    const nodeIdSet = new Set(nodeIds)
    return edges.value.filter(e =>
      nodeIdSet.has(e.source) && nodeIdSet.has(e.target)
    )
  }

  /**
   * Copy selected nodes to clipboard
   * @returns {Promise<boolean>} True if copy succeeded
   */
  async function copySelectedNodes() {
    const selectedNodes = getSelectedNodes()

    if (selectedNodes.length === 0) {
      return false
    }

    isCopying.value = true

    try {
      // Get node IDs
      const nodeIds = selectedNodes.map(n => n.id)

      // Get edges between selected nodes
      const connectedEdges = getConnectedEdges(nodeIds)

      // Prepare clipboard data
      const clipboardData = {
        marker: CLIPBOARD_MARKER,
        timestamp: Date.now(),
        nodes: selectedNodes.map(n => deepClone(n)),
        edges: connectedEdges.map(e => deepClone(e))
      }

      // Write to clipboard
      await navigator.clipboard.writeText(JSON.stringify(clipboardData))

      return true
    } catch (error) {
      console.error('[useClipboard] Failed to copy:', error)
      return false
    } finally {
      isCopying.value = false
    }
  }

  /**
   * Paste nodes from clipboard
   * @param {Object} options
   * @param {Object} options.position - Paste position { x, y }
   * @returns {Promise<{ nodes: Array, edges: Array } | null>} Pasted nodes/edges or null
   */
  async function pasteNodes(options = {}) {
    isPasting.value = true

    try {
      // Read from clipboard
      const clipboardText = await navigator.clipboard.readText()

      // Try to parse as JSON
      let clipboardData
      try {
        clipboardData = JSON.parse(clipboardText)
      } catch {
        return null
      }

      // Validate clipboard data
      if (!clipboardData || clipboardData.marker !== CLIPBOARD_MARKER) {
        return null
      }

      if (!clipboardData.nodes || clipboardData.nodes.length === 0) {
        return null
      }

      // Call before paste hook (for history)
      onBeforePaste?.()

      // Calculate paste offset
      const offset = calculatePasteOffset(clipboardData.nodes, options.position)

      // Create ID mapping (old ID -> new ID)
      const idMap = new Map()
      clipboardData.nodes.forEach(node => {
        idMap.set(node.id, generateNodeId())
      })

      // Create new nodes with new IDs and offset positions
      const newNodes = clipboardData.nodes.map(node => ({
        ...node,
        id: idMap.get(node.id),
        position: {
          x: node.position.x + offset.x,
          y: node.position.y + offset.y
        },
        selected: true,
        // Clear execution state
        data: {
          ...node.data,
          executionState: null,
          status: null
        }
      }))

      // Create new edges with updated source/target IDs
      const newEdges = clipboardData.edges.map(edge => ({
        ...edge,
        id: `${idMap.get(edge.source)}-${idMap.get(edge.target)}-${Date.now()}`,
        source: idMap.get(edge.source),
        target: idMap.get(edge.target)
      }))

      // Deselect existing nodes
      nodes.value = nodes.value.map(n => ({ ...n, selected: false }))

      // Add new nodes and edges
      nodes.value = [...nodes.value, ...newNodes]
      edges.value = [...edges.value, ...newEdges]

      // Update last paste position for subsequent pastes
      lastPastePosition.value = {
        x: lastPastePosition.value.x + 40,
        y: lastPastePosition.value.y + 40
      }

      // Sync to parent
      onSync?.()

      return { nodes: newNodes, edges: newEdges }
    } catch (error) {
      console.error('[useClipboard] Failed to paste:', error)
      return null
    } finally {
      isPasting.value = false
    }
  }

  /**
   * Calculate offset for pasting nodes
   */
  function calculatePasteOffset(sourceNodes, targetPosition) {
    if (targetPosition) {
      // Paste at specified position
      const minX = Math.min(...sourceNodes.map(n => n.position.x))
      const minY = Math.min(...sourceNodes.map(n => n.position.y))
      return {
        x: targetPosition.x - minX,
        y: targetPosition.y - minY
      }
    }

    // Default: offset by 40px from last paste or original position
    return {
      x: lastPastePosition.value.x || 40,
      y: lastPastePosition.value.y || 40
    }
  }

  /**
   * Cut selected nodes (copy then delete)
   * @param {Function} deleteCallback - Callback to delete nodes
   * @returns {Promise<boolean>} True if cut succeeded
   */
  async function cutSelectedNodes(deleteCallback) {
    const success = await copySelectedNodes()
    if (success && deleteCallback) {
      const selectedNodes = getSelectedNodes()
      selectedNodes.forEach(node => deleteCallback(node.id))
    }
    return success
  }

  /**
   * Reset paste position (call when changing workflows)
   */
  function resetPastePosition() {
    lastPastePosition.value = { x: 40, y: 40 }
  }

  /**
   * Check if clipboard has workflow data
   * @returns {Promise<boolean>}
   */
  async function hasWorkflowData() {
    try {
      const clipboardText = await navigator.clipboard.readText()
      const data = JSON.parse(clipboardText)
      return data?.marker === CLIPBOARD_MARKER
    } catch {
      return false
    }
  }

  return {
    // State
    isCopying,
    isPasting,

    // Actions
    copySelectedNodes,
    pasteNodes,
    cutSelectedNodes,
    resetPastePosition,
    hasWorkflowData
  }
}

export default useClipboard
