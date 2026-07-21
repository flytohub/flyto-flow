/**
 * Workflow Execution Actions
 *
 * S-Grade: Workflow execution operations.
 * Single responsibility: Execution management.
 */

import { workflowAPI } from '@/api/workflows'
import i18n from '@/i18n'
import { trackWorkflow } from '@/utils/telemetryTracker'

/**
 * Create workflow execution action handlers
 * @param {Object} state - State refs
 * @returns {Object} Execution action functions
 */
export function createWorkflowExecutionActions(state) {
  const { isLoading, error, executionStatus, executionLogs, executionProgress } = state

  /**
   * Execute workflow
   */
  async function executeWorkflow(id, context = {}) {
    isLoading.value = true
    error.value = null
    executionStatus.value = 'running'
    executionLogs.value = []
    executionProgress.value = 0

    const startTime = Date.now()
    trackWorkflow.executeStart(id, null, context.trigger || 'manual')

    try {
      const data = await workflowAPI.execute(id, context)
      executionStatus.value = 'success'
      executionProgress.value = 100

      trackWorkflow.executeComplete(id, Date.now() - startTime, null)

      return data
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToExecuteWorkflow')
      executionStatus.value = 'failed'

      trackWorkflow.executeError(id, err.message, null)

      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Stop workflow execution
   */
  async function stopExecution(id) {
    try {
      await workflowAPI.stop(id)
      executionStatus.value = 'stopped'
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToStopWorkflow')
      throw err
    }
  }

  /**
   * Add execution log entry
   */
  function addExecutionLog(log) {
    executionLogs.value.push({
      timestamp: new Date().toISOString(),
      message: log
    })
  }

  /**
   * Update execution progress
   */
  function updateExecutionProgress(progress) {
    executionProgress.value = Math.min(100, Math.max(0, progress))
  }

  /**
   * Reset execution state
   */
  function resetExecutionState() {
    executionStatus.value = null
    executionLogs.value = []
    executionProgress.value = 0
  }

  return {
    executeWorkflow,
    stopExecution,
    addExecutionLog,
    updateExecutionProgress,
    resetExecutionState
  }
}
