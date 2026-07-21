/**
 * Debug Selection Composable
 * Manages debug mode selection state for workflow canvas
 */

import { ref, watch } from 'vue'

export function useDebugSelection(nodes, emit, props) {
  const isSelecting = ref(false)

  // Watch debugMode changes to update node data
  watch(() => props.debugMode, (newVal) => {
    if (!newVal) {
      // Clear debug selection when exiting debug mode
      nodes.value = nodes.value.map(n => ({
        ...n,
        data: { ...n.data, debugSelected: false }
      }))
    }
  })

  // Watch debugSelectedNodes from parent to sync
  watch(() => props.debugSelectedNodes, (selectedIds) => {
    nodes.value = nodes.value.map(n => ({
      ...n,
      data: { ...n.data, debugSelected: selectedIds.includes(n.id) }
    }))
  }, { deep: true })

  // Selection event handlers for debug mode
  function onSelectionStart(event) {
    if (props.debugMode) {
      isSelecting.value = true
    }
  }

  function onSelectionEnd(event) {
    if (props.debugMode) {
      isSelecting.value = false
      // Get selected nodes from VueFlow internal selection
      const selectedNodes = nodes.value.filter(n => n.selected)
      if (selectedNodes.length > 0) {
        // Update node data to show debug selection
        const selectedIds = selectedNodes.map(n => n.id)
        nodes.value = nodes.value.map(n => ({
          ...n,
          selected: false, // Clear VueFlow selection
          data: { ...n.data, debugSelected: selectedIds.includes(n.id) }
        }))
        // Emit to parent
        emit('debug-selection-change', selectedIds)
      }
    }
  }

  function onSelectionDragStart(event) {
    if (props.debugMode) {
      isSelecting.value = true
    }
  }

  function handleDebugNodeClick(nodeId) {
    const currentSelected = props.debugSelectedNodes || []
    let newSelected

    if (currentSelected.includes(nodeId)) {
      // Remove from selection
      newSelected = currentSelected.filter(id => id !== nodeId)
    } else {
      // Add to selection
      newSelected = [...currentSelected, nodeId]
    }

    // Update node data to show debug selection
    nodes.value = nodes.value.map(n => ({
      ...n,
      data: { ...n.data, debugSelected: newSelected.includes(n.id) }
    }))

    emit('debug-selection-change', newSelected)
  }

  return {
    isSelecting,
    onSelectionStart,
    onSelectionEnd,
    onSelectionDragStart,
    handleDebugNodeClick
  }
}
