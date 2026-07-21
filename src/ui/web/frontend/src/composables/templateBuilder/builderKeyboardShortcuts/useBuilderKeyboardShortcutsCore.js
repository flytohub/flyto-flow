/**
 * Builder Keyboard Shortcuts Core
 *
 * S-Grade: Main keyboard shortcuts composable for Template Builder.
 * Single responsibility: Compose keyboard shortcut functionality.
 */

import { computed, watch } from 'vue'
import { useKeyboardShortcuts, useClipboard, useHistory } from '../../useKeyboardShortcuts'
import { createHandlers } from './handlers'

/**
 * Create keyboard shortcuts for Template Builder
 *
 * @param {Object} options
 * @param {Ref} options.activeTab - Current active tab ('ui' or 'workflow')
 * @param {Ref} options.selectedComponentLocation - Selected UI component location
 * @param {Ref} options.selectedWorkflowNode - Selected workflow node
 * @param {Ref} options.sections - UI sections data
 * @param {Ref} options.elements - Workflow elements (nodes + edges)
 * @param {Function} options.deleteComponent - Delete UI component function
 * @param {Function} options.duplicateComponent - Duplicate UI component function
 * @param {Function} options.saveTemplate - Save template function
 * @param {Function} options.showToast - Toast notification function
 * @param {Function} options.deleteNode - Delete workflow node function
 */
export function useBuilderKeyboardShortcuts(options) {
  const {
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
  } = options

  // Clipboard for component/node copying
  const clipboard = useClipboard()

  // History for undo/redo
  const history = useHistory({ maxSize: 30 })

  // Track if we should save history on next change
  let shouldTrackHistory = true

  function setShouldTrackHistory(value) {
    shouldTrackHistory = value
  }

  /**
   * Get currently selected item for operations
   */
  const selectedItem = computed(() => {
    if (activeTab.value === 'ui' && selectedComponentLocation.value) {
      const { sectionIndex, columnIndex, componentIndex } = selectedComponentLocation.value
      const section = sections.value?.[sectionIndex]
      const column = section?.columnsData?.[columnIndex]
      return column?.components?.[componentIndex] || null
    }
    if (activeTab.value === 'workflow' && selectedWorkflowNode.value) {
      return selectedWorkflowNode.value
    }
    return null
  })

  /**
   * Save current state to history
   */
  function saveHistorySnapshot() {
    if (!shouldTrackHistory) return

    const state = {
      tab: activeTab.value,
      sections: JSON.parse(JSON.stringify(sections.value || [])),
      elements: JSON.parse(JSON.stringify(elements.value || [])),
    }
    history.push(state)
  }

  // Create handlers
  const handlers = createHandlers({
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
  })

  // Setup keyboard shortcuts
  const { availableShortcuts, getShortcutDisplay, isMac } = useKeyboardShortcuts(
    {
      copy: handlers.handleCopy,
      cut: handlers.handleCut,
      paste: handlers.handlePaste,
      undo: handlers.handleUndo,
      redo: handlers.handleRedo,
      delete: handlers.handleDelete,
      save: handlers.handleSave,
      duplicate: handlers.handleDuplicate,
      escape: handlers.handleEscape,
    },
    {
      ignoreInputs: true,
    }
  )

  // Watch for changes to save history
  watch(
    () => [sections.value, elements.value],
    () => {
      if (shouldTrackHistory) {
        saveHistorySnapshot()
      }
    },
    { deep: true }
  )

  // Initial history snapshot
  saveHistorySnapshot()

  return {
    clipboard,
    history,
    availableShortcuts,
    getShortcutDisplay,
    isMac,
    canUndo: history.canUndo,
    canRedo: history.canRedo,
    hasClipboard: clipboard.hasData,
  }
}
