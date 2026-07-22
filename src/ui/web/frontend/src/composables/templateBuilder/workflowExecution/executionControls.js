/**
 * Execution Controls
 *
 * S-Grade: Workflow execution control handlers.
 * Single responsibility: Run, stop, pause, resume workflow.
 */

/**
 * Create execution control handlers
 * @param {Object} deps - Dependencies
 * @param {Function} deps.executeWorkflow - Execute workflow function
 * @param {Function} deps.stopWorkflowExecution - Stop execution function
 * @param {Function} deps.pauseExecution - Pause execution function
 * @param {Function} deps.stepExecution - Step execution function
 * @param {Function} deps.resumeExecution - Resume execution function
 * @param {Function} deps.runToEndExecution - Run to end function
 * @param {Function} deps.showToast - Toast notification function
 * @param {Function} deps.t - i18n translate function
 * @returns {Object} Control handler functions
 */
export function createExecutionControls(deps) {
  const {
    executeWorkflow,
    stopWorkflowExecution,
    pauseExecution,
    stepExecution,
    resumeExecution,
    runToEndExecution,
    showToast,
    t
  } = deps

  /**
   * Run the workflow
   */
  async function runWorkflow(options) {
    const { elements, templateId, templateName, uiInputValues, checkpoints } = options

    const result = await executeWorkflow({
      elements: elements.value,
      templateId: templateId.value,
      templateName: templateName.value,
      uiInputValues,
      checkpoints
    })

    if (!result.ok) {
      if (result.error === 'NO_STEPS') {
        showToast(t('templateBuilder.messages.noStepsToExecute'), 'warning')
      } else if (result.error === 'NO_VALID_STEPS') {
        showToast(t('templateBuilder.messages.noValidSteps'), 'warning')
      } else {
        showToast(t('templateBuilder.messages.executionFailed', { error: result.error }), 'error')
      }
    } else {
      showToast(t('templateBuilder.messages.startingExecution'), 'info')
    }

    return result
  }

  /**
   * Stop the workflow execution
   */
  async function stopExecution() {
    const result = await stopWorkflowExecution()
    if (result.cancelled) {
      showToast(t('templateBuilder.messages.executionCancelled'), 'info')
    } else {
      showToast(t('templateBuilder.messages.executionStopped'), 'warning')
    }
    return result
  }

  /**
   * Pause execution
   */
  async function handlePause() {
    const result = await pauseExecution()
    if (result.ok) {
      showToast(t('templateBuilder.messages.executionPaused', 'Execution paused'), 'info')
    } else {
      showToast(result.error || t('templateBuilder.messages.pauseFailed', 'Failed to pause'), 'error')
    }
    return result
  }

  /**
   * Step execution (execute one step then pause)
   */
  async function handleStep() {
    const result = await stepExecution()
    if (result.ok) {
      showToast(t('templateBuilder.messages.stepExecuted', 'Step executed'), 'info')
    } else {
      showToast(result.error || t('templateBuilder.messages.stepFailed', 'Failed to step'), 'error')
    }
    return result
  }

  /**
   * Stop execution (alias)
   */
  async function handleStop() {
    return stopExecution()
  }

  /**
   * Resume execution
   */
  async function handleResume() {
    const result = await resumeExecution()
    if (result.ok) {
      showToast(t('templateBuilder.messages.executionResumed', 'Execution resumed'), 'info')
    } else {
      showToast(result.error || t('templateBuilder.messages.resumeFailed', 'Failed to resume'), 'error')
    }
    return result
  }

  /**
   * Run to end
   */
  async function handleRunToEnd() {
    const result = await runToEndExecution()
    if (result.ok) {
      showToast(t('templateBuilder.messages.runningToEnd', 'Running to completion...'), 'info')
    } else {
      showToast(result.error || t('templateBuilder.messages.runToEndFailed', 'Failed to run to end'), 'error')
    }
    return result
  }

  return {
    runWorkflow,
    stopExecution,
    handlePause,
    handleStep,
    handleStop,
    handleResume,
    handleRunToEnd,
  }
}
