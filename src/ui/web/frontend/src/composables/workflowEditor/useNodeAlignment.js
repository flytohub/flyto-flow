/**
 * Node Alignment Composable
 *
 * Provides alignment and distribution functions for selected workflow nodes.
 * Similar to professional design tools like Figma/Sketch.
 */

import { computed } from 'vue'
import { useModulesStore } from '@/stores/modulesStore'

/**
 * Create node alignment utilities
 * @param {Ref<Array>} nodes - Reactive nodes array
 * @param {Function} onSync - Callback to sync changes to parent
 * @param {Function} saveHistory - I5 fix: Optional callback to save history before alignment
 * @returns {Object} Alignment functions
 */
export function useNodeAlignment(nodes, onSync, saveHistory = null) {
  const modulesStore = useModulesStore()

  // Get per-node dimensions from backend SSOT (enriched in modulesMetadata)
  function _getNodeDims(node) {
    const dims = modulesStore.modulesMetadata?.[node.data?.module]?.uiConfig?.dimensions
    return { width: dims?.width ?? 240, height: dims?.height ?? 76 }
  }

  // Get selected nodes
  const selectedNodes = computed(() =>
    nodes.value.filter(node => node.selected)
  )

  // Check if alignment is possible (need 2+ selected nodes)
  const canAlign = computed(() => selectedNodes.value.length >= 2)

  // Check if distribution is possible (need 3+ selected nodes)
  const canDistribute = computed(() => selectedNodes.value.length >= 3)

  /**
   * Get bounding box of selected nodes (per-node dimensions from backend SSOT)
   */
  function getBoundingBox() {
    const selected = selectedNodes.value
    if (selected.length === 0) return null

    return {
      minX: Math.min(...selected.map(n => n.position.x)),
      maxX: Math.max(...selected.map(n => n.position.x + _getNodeDims(n).width)),
      minY: Math.min(...selected.map(n => n.position.y)),
      maxY: Math.max(...selected.map(n => n.position.y + _getNodeDims(n).height)),
    }
  }

  /**
   * Align selected nodes to the left edge
   * I5 fix: Save history before alignment for undo support
   */
  function alignLeft() {
    if (!canAlign.value) return

    // I5 fix: Save history before alignment
    saveHistory?.('NODE_MOVE', { type: 'align-left', nodeIds: selectedNodes.value.map(n => n.id) })

    const minX = Math.min(...selectedNodes.value.map(n => n.position.x))

    nodes.value = nodes.value.map(node => {
      if (node.selected) {
        return {
          ...node,
          position: { ...node.position, x: minX }
        }
      }
      return node
    })

    onSync?.()
  }

  /**
   * Align selected nodes to the right edge
   * I5 fix: Save history before alignment for undo support
   */
  function alignRight() {
    if (!canAlign.value) return

    // I5 fix: Save history before alignment
    saveHistory?.('NODE_MOVE', { type: 'align-right', nodeIds: selectedNodes.value.map(n => n.id) })

    const maxX = Math.max(...selectedNodes.value.map(n => n.position.x))

    nodes.value = nodes.value.map(node => {
      if (node.selected) {
        return {
          ...node,
          position: { ...node.position, x: maxX }
        }
      }
      return node
    })

    onSync?.()
  }

  /**
   * Align selected nodes to the top edge
   * I5 fix: Save history before alignment for undo support
   */
  function alignTop() {
    if (!canAlign.value) return

    // I5 fix: Save history before alignment
    saveHistory?.('NODE_MOVE', { type: 'align-top', nodeIds: selectedNodes.value.map(n => n.id) })

    const minY = Math.min(...selectedNodes.value.map(n => n.position.y))

    nodes.value = nodes.value.map(node => {
      if (node.selected) {
        return {
          ...node,
          position: { ...node.position, y: minY }
        }
      }
      return node
    })

    onSync?.()
  }

  /**
   * Align selected nodes to the bottom edge
   * I5 fix: Save history before alignment for undo support
   */
  function alignBottom() {
    if (!canAlign.value) return

    // I5 fix: Save history before alignment
    saveHistory?.('NODE_MOVE', { type: 'align-bottom', nodeIds: selectedNodes.value.map(n => n.id) })

    const maxY = Math.max(...selectedNodes.value.map(n => n.position.y))

    nodes.value = nodes.value.map(node => {
      if (node.selected) {
        return {
          ...node,
          position: { ...node.position, y: maxY }
        }
      }
      return node
    })

    onSync?.()
  }

  /**
   * Align selected nodes to horizontal center
   * I5 fix: Save history before alignment for undo support
   */
  function alignCenterH() {
    if (!canAlign.value) return

    // I5 fix: Save history before alignment
    saveHistory?.('NODE_MOVE', { type: 'align-center-h', nodeIds: selectedNodes.value.map(n => n.id) })

    const selected = selectedNodes.value
    const avgX = selected.reduce((sum, n) => sum + n.position.x, 0) / selected.length

    nodes.value = nodes.value.map(node => {
      if (node.selected) {
        return {
          ...node,
          position: { ...node.position, x: avgX }
        }
      }
      return node
    })

    onSync?.()
  }

  /**
   * Align selected nodes to vertical center
   * I5 fix: Save history before alignment for undo support
   */
  function alignCenterV() {
    if (!canAlign.value) return

    // I5 fix: Save history before alignment
    saveHistory?.('NODE_MOVE', { type: 'align-center-v', nodeIds: selectedNodes.value.map(n => n.id) })

    const selected = selectedNodes.value
    const avgY = selected.reduce((sum, n) => sum + n.position.y, 0) / selected.length

    nodes.value = nodes.value.map(node => {
      if (node.selected) {
        return {
          ...node,
          position: { ...node.position, y: avgY }
        }
      }
      return node
    })

    onSync?.()
  }

  /**
   * Distribute selected nodes evenly horizontally
   * I5 fix: Save history before distribution for undo support
   */
  function distributeHorizontal() {
    if (!canDistribute.value) return

    // I5 fix: Save history before distribution
    saveHistory?.('NODE_MOVE', { type: 'distribute-h', nodeIds: selectedNodes.value.map(n => n.id) })

    const selected = [...selectedNodes.value].sort((a, b) => a.position.x - b.position.x)
    const minX = selected[0].position.x
    const maxX = selected[selected.length - 1].position.x
    const gap = (maxX - minX) / (selected.length - 1)

    const newPositions = new Map()
    selected.forEach((node, index) => {
      newPositions.set(node.id, minX + gap * index)
    })

    nodes.value = nodes.value.map(node => {
      if (node.selected && newPositions.has(node.id)) {
        return {
          ...node,
          position: { ...node.position, x: newPositions.get(node.id) }
        }
      }
      return node
    })

    onSync?.()
  }

  /**
   * Distribute selected nodes evenly vertically
   * I5 fix: Save history before distribution for undo support
   */
  function distributeVertical() {
    if (!canDistribute.value) return

    // I5 fix: Save history before distribution
    saveHistory?.('NODE_MOVE', { type: 'distribute-v', nodeIds: selectedNodes.value.map(n => n.id) })

    const selected = [...selectedNodes.value].sort((a, b) => a.position.y - b.position.y)
    const minY = selected[0].position.y
    const maxY = selected[selected.length - 1].position.y
    const gap = (maxY - minY) / (selected.length - 1)

    const newPositions = new Map()
    selected.forEach((node, index) => {
      newPositions.set(node.id, minY + gap * index)
    })

    nodes.value = nodes.value.map(node => {
      if (node.selected && newPositions.has(node.id)) {
        return {
          ...node,
          position: { ...node.position, y: newPositions.get(node.id) }
        }
      }
      return node
    })

    onSync?.()
  }

  return {
    // State
    selectedNodes,
    canAlign,
    canDistribute,

    // Alignment functions
    alignLeft,
    alignRight,
    alignTop,
    alignBottom,
    alignCenterH,
    alignCenterV,

    // Distribution functions
    distributeHorizontal,
    distributeVertical,

    // Utility
    getBoundingBox
  }
}
