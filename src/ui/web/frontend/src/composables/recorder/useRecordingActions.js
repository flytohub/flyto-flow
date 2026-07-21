/**
 * Recording Actions Composable
 *
 * Manages recorded action operations: add, edit, delete, select.
 */

import { useI18n } from 'vue-i18n'

export function useRecordingActions({
  recordedActions,
  selectedAction,
  editingAction,
  emit
}) {
  const { t } = useI18n()

  /**
   * Add a new action
   */
  function addAction(action) {
    const formattedAction = {
      type: action.type,
      selector: action.selector,
      value: action.value,
      timestamp: Date.now(),
      options: action.options || {}
    }
    recordedActions.value.push(formattedAction)
    if (emit) emit('action-recorded', formattedAction)
  }

  /**
   * Select an action for editing
   */
  function selectAction(index) {
    selectedAction.value = index
    editingAction.value = { ...recordedActions.value[index] }
  }

  /**
   * Save edited action
   */
  function saveEdit() {
    if (selectedAction.value !== null) {
      recordedActions.value[selectedAction.value] = { ...editingAction.value }
      selectedAction.value = null
      editingAction.value = {}
    }
  }

  /**
   * Cancel edit
   */
  function cancelEdit() {
    selectedAction.value = null
    editingAction.value = {}
  }

  /**
   * Delete an action
   */
  function deleteAction(index) {
    recordedActions.value.splice(index, 1)
    if (selectedAction.value === index) {
      selectedAction.value = null
      editingAction.value = {}
    }
  }

  /**
   * Clear all actions
   */
  function clearActions() {
    if (confirm(t('recorder.clearConfirm'))) {
      recordedActions.value = []
      selectedAction.value = null
      editingAction.value = {}
    }
  }

  return {
    addAction,
    selectAction,
    saveEdit,
    cancelEdit,
    deleteAction,
    clearActions
  }
}
