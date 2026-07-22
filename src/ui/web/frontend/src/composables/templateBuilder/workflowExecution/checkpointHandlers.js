/**
 * Checkpoint Handlers
 *
 * S-Grade: Checkpoint and recovery operations.
 * Single responsibility: Handle checkpoint resume, retry, dismiss.
 */

/**
 * Create checkpoint handler functions
 * @param {Object} deps - Dependencies
 * @param {Function} deps.resumeFromCheckpoint - Resume from checkpoint function
 * @param {Object} deps.controlStore - Execution control store
 * @param {Object} deps.builderStore - Builder store
 * @param {Function} deps.showToast - Toast notification function
 * @param {Function} deps.t - i18n translate function
 * @param {Function} deps.runWorkflow - Run workflow function
 * @returns {Object} Checkpoint handler functions
 */
export function createCheckpointHandlers(deps) {
  const {
    resumeFromCheckpoint,
    controlStore,
    builderStore,
    showToast,
    t,
    runWorkflow
  } = deps

  /**
   * Resume from checkpoint after failure
   */
  async function handleResumeFromCheckpoint(checkpointId) {
    const result = await resumeFromCheckpoint(checkpointId)
    if (result.ok) {
      showToast(t('templateBuilder.messages.executionResumed', 'Execution resumed from checkpoint'), 'info')
    } else {
      showToast(result.error || t('templateBuilder.messages.resumeFailed', 'Failed to resume'), 'error')
    }
    return result
  }

  /**
   * Retry execution from the beginning
   */
  async function handleRetryExecution() {
    // Reset the control store and run the workflow again
    controlStore.reset()
    await runWorkflow()
  }

  /**
   * Dismiss the resume panel (user abandons recovery)
   */
  function dismissResumePanel() {
    // Reset the control store to dismiss the panel
    controlStore.reset()
  }

  /**
   * Toggle checkpoint on a node
   */
  function handleToggleCheckpoint(nodeId) {
    builderStore.toggleCheckpoint(nodeId)
  }

  /**
   * Continue from checkpoint
   */
  async function handleContinueFromCheckpoint() {
    const result = await controlStore.continueFromCheckpoint()
    if (!result) {
      showToast(controlStore.error || 'Failed to continue', 'error')
    }
    return result
  }

  /**
   * Bypass checkpoint
   */
  async function handleBypassCheckpoint(scope) {
    const result = await controlStore.bypassCheckpoint(scope)
    if (result) {
      const scopeText = scope === 'this_run' ? 'this run' : 'this workflow version'
      showToast(`Checkpoint bypassed for ${scopeText}`, 'info')
    } else {
      showToast(controlStore.error || 'Failed to bypass checkpoint', 'error')
    }
    return result
  }

  return {
    handleResumeFromCheckpoint,
    handleRetryExecution,
    dismissResumePanel,
    handleToggleCheckpoint,
    handleContinueFromCheckpoint,
    handleBypassCheckpoint,
  }
}
