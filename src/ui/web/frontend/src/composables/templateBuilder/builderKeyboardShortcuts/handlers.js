/**
 * Builder Keyboard Shortcuts Handlers
 *
 * S-Grade: Keyboard shortcut action handlers.
 * Single responsibility: Handle copy, paste, undo, redo, delete, save operations.
 */

import { generateNodeId } from '@/composables/workflowEditor/canvasOps/nodeUtils'

/** Offset for pasted/duplicated nodes */
const NODE_PASTE_OFFSET = { x: 40, y: 40 }

/**
 * Create keyboard shortcut handlers
 * @param {Object} deps - Dependencies
 * @param {Object} deps.clipboard - Clipboard manager
 * @param {Object} deps.history - History manager
 * @param {Ref} deps.activeTab - Current active tab
 * @param {Ref} deps.selectedComponentLocation - Selected UI component location
 * @param {Ref} deps.selectedWorkflowNode - Selected workflow node
 * @param {Ref} deps.sections - UI sections data
 * @param {Ref} deps.elements - Workflow elements
 * @param {Function} deps.deleteComponent - Delete UI component function
 * @param {Function} deps.duplicateComponent - Duplicate UI component function
 * @param {Function} deps.saveTemplate - Save template function
 * @param {Function} deps.showToast - Toast notification function
 * @param {Function} deps.deleteNode - Delete workflow node function
 * @param {Function} deps.saveHistorySnapshot - Save history snapshot function
 * @param {Ref} deps.selectedItem - Currently selected item
 * @returns {Object} Handler functions
 */
export function createHandlers(deps) {
  const {
    clipboard,
    history,
    activeTab,
    selectedComponentLocation,
    selectedWorkflowNode,
    sections,
    elements,
    deleteComponent,
    duplicateComponent,
    saveTemplate,
    showToast,
    deleteNode,
    saveHistorySnapshot,
    selectedItem,
    setShouldTrackHistory
  } = deps

  /**
   * Handle copy action
   */
  function handleCopy() {
    if (!selectedItem.value) {
      showToast?.('Nothing selected to copy', 'info')
      return
    }

    clipboard.copy({
      type: activeTab.value === 'ui' ? 'component' : 'node',
      data: selectedItem.value,
      location: activeTab.value === 'ui' ? selectedComponentLocation.value : null,
    })

    showToast?.('Copied to clipboard', 'success')
  }

  /**
   * Handle paste action
   */
  function handlePaste() {
    const item = clipboard.paste()
    if (!item) {
      showToast?.('Nothing to paste', 'info')
      return
    }

    // Handle UI component paste
    if (item.type === 'component' && activeTab.value === 'ui') {
      if (!selectedComponentLocation.value) {
        showToast?.('Select a column first', 'warning')
        return
      }

      saveHistorySnapshot()

      const { sectionIndex, columnIndex } = selectedComponentLocation.value
      const section = sections.value?.[sectionIndex]
      const column = section?.columnsData?.[columnIndex]

      if (column) {
        // Create a copy with new ID
        const newComponent = JSON.parse(JSON.stringify(item.data))
        newComponent.id = `${newComponent.type}_${Date.now()}`
        newComponent.label = `${newComponent.label || newComponent.type} (Pasted)`

        column.components.push(newComponent)
        showToast?.('Component pasted', 'success')
      }
    }

    // Handle workflow node paste
    if (item.type === 'node' && activeTab.value === 'workflow') {
      saveHistorySnapshot()

      const sourceNode = item.data
      const newNode = createPastedNode(sourceNode)

      elements.value = [...elements.value, newNode]
      showToast?.('Node pasted', 'success')
    }
  }

  /**
   * Create a pasted node with new ID and offset position
   * @param {Object} sourceNode - Original node to copy
   * @returns {Object} New node object
   */
  function createPastedNode(sourceNode) {
    const newId = generateNodeId()
    return {
      ...JSON.parse(JSON.stringify(sourceNode)),
      id: newId,
      position: {
        x: (sourceNode.position?.x || 200) + NODE_PASTE_OFFSET.x,
        y: (sourceNode.position?.y || 100) + NODE_PASTE_OFFSET.y
      },
      data: {
        ...sourceNode.data
      }
    }
  }

  /**
   * Handle undo action
   */
  function handleUndo() {
    if (!history.canUndo.value) {
      showToast?.('Nothing to undo', 'info')
      return
    }

    setShouldTrackHistory(false)
    const state = history.undo()

    if (state) {
      sections.value = state.sections
      elements.value = state.elements
      showToast?.('Undone', 'success')
    }

    setShouldTrackHistory(true)
  }

  /**
   * Handle redo action
   */
  function handleRedo() {
    if (!history.canRedo.value) {
      showToast?.('Nothing to redo', 'info')
      return
    }

    setShouldTrackHistory(false)
    const state = history.redo()

    if (state) {
      sections.value = state.sections
      elements.value = state.elements
      showToast?.('Redone', 'success')
    }

    setShouldTrackHistory(true)
  }

  /**
   * Handle delete action
   */
  function handleDelete() {
    if (!selectedItem.value) return

    if (activeTab.value === 'ui' && selectedComponentLocation.value) {
      const { sectionIndex, columnIndex, componentIndex } = selectedComponentLocation.value
      deleteComponent?.(sectionIndex, columnIndex, componentIndex)
    } else if (activeTab.value === 'workflow' && selectedWorkflowNode.value) {
      deleteNode?.(selectedWorkflowNode.value.id)
    }
  }

  /**
   * Handle save action
   */
  function handleSave(e) {
    e?.preventDefault()
    saveTemplate?.()
  }

  /**
   * Handle duplicate action
   */
  function handleDuplicate() {
    if (!selectedItem.value) return

    if (activeTab.value === 'ui' && selectedComponentLocation.value) {
      const { sectionIndex, columnIndex, componentIndex } = selectedComponentLocation.value
      duplicateComponent?.(sectionIndex, columnIndex, componentIndex)
    }

    // Handle workflow node duplication
    if (activeTab.value === 'workflow' && selectedWorkflowNode.value) {
      saveHistorySnapshot()

      const sourceNode = selectedWorkflowNode.value
      const newNode = createPastedNode(sourceNode)

      elements.value = [...elements.value, newNode]
      showToast?.('Node duplicated', 'success')
    }
  }

  /**
   * Handle escape action
   */
  function handleEscape() {
    // Deselect current selection
    if (activeTab.value === 'ui') {
      selectedComponentLocation.value = null
    } else if (activeTab.value === 'workflow') {
      selectedWorkflowNode.value = null
    }
  }

  /**
   * Handle cut action (copy + delete)
   */
  function handleCut() {
    if (!selectedItem.value) {
      showToast?.('Nothing selected to cut', 'info')
      return
    }

    // First copy the item
    clipboard.copy({
      type: activeTab.value === 'ui' ? 'component' : 'node',
      data: selectedItem.value,
      location: activeTab.value === 'ui' ? selectedComponentLocation.value : null,
    })

    // Then delete it
    handleDelete()

    showToast?.('Cut to clipboard', 'success')
  }

  return {
    handleCopy,
    handleCut,
    handlePaste,
    handleUndo,
    handleRedo,
    handleDelete,
    handleSave,
    handleDuplicate,
    handleEscape
  }
}
