/**
 * Navigation Actions
 *
 * S-Grade: Navigation with unsaved changes handling.
 * Single responsibility: Handle back/leave navigation.
 */

/**
 * Create navigation action handlers
 * @param {Object} options
 * @param {Ref} options.hasUnsavedChanges - Unsaved changes flag
 * @param {Ref} options.showSaveDialog - Save dialog visibility
 * @param {Function} options.saveTemplate - Save function
 * @param {Object} options.router - Vue router instance
 * @returns {Object} Navigation action functions
 */
export function createNavigationActions(options) {
  const { hasUnsavedChanges, showSaveDialog, saveTemplate, router } = options

  /**
   * Handle back navigation
   */
  function handleBack() {
    if (hasUnsavedChanges.value) {
      showSaveDialog.value = true
    } else {
      router.push('/my-templates')
    }
  }

  /**
   * Leave without saving
   */
  function leaveWithoutSaving() {
    showSaveDialog.value = false
    hasUnsavedChanges.value = false
    router.push('/my-templates')
  }

  /**
   * Save and then leave
   */
  async function saveAndLeave() {
    showSaveDialog.value = false
    const result = await saveTemplate()
    // Only clear unsaved changes if save succeeded
    if (result && result.ok !== false) {
      hasUnsavedChanges.value = false
      router.push('/my-templates')
    }
    // If save failed, dialog is already closed and user stays on page
  }

  return {
    handleBack,
    leaveWithoutSaving,
    saveAndLeave
  }
}
