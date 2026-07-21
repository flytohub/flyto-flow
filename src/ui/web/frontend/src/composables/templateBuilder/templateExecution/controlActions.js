/**
 * Execution Control Actions
 *
 * S-Grade: Execution control actions.
 * Single responsibility: Stop, pause, resume, step execution.
 */

import * as executionAPI from '@/api/executions'
import { runToEnd as runToEndAPI } from '@/api/executions'

/**
 * Create execution control actions
 * @param {Object} state - State refs
 * @param {Object} computed - Computed properties
 * @param {Object} pollingActions - Polling actions
 * @param {Object} controlStore - Execution control store
 * @returns {Object} Control actions
 */
export function createControlActions(state, computed, pollingActions, controlStore) {
  const {
    isExecuting,
    currentExecutionId,
    executionStatus
  } = state
  const { canPause, canResume, canStep } = computed
  const { resetExecutionState, startExecutionPolling } = pollingActions

  /**
   * Stop execution
   * @returns {Promise<Object>} Stop result
   */
  async function stopExecution() {
    if (!currentExecutionId.value) {
      resetExecutionState()
      return { ok: true, cancelled: false }
    }

    try {
      const data = await executionAPI.cancelExecution(currentExecutionId.value)
      resetExecutionState()
      return { ok: true, cancelled: data.ok }
    } catch (error) {
      resetExecutionState()
      return { ok: false, error: error.message }
    }
  }

  /**
   * Pause execution
   * FE-P1-012: Sync execution status with store and state
   * @returns {Promise<Object>} Pause result
   */
  async function pauseExecution() {
    if (!currentExecutionId.value || !canPause.value) {
      return { ok: false, error: 'Cannot pause' }
    }

    try {
      const result = await executionAPI.pauseExecution(currentExecutionId.value)
      if (result.ok) {
        executionStatus.value = 'paused'
        // FE-P1-012: Keep isExecuting true while paused (execution is paused, not stopped)
        isExecuting.value = true
        controlStore.setExecution(currentExecutionId.value, 'paused')
      }
      return result
    } catch (error) {
      return { ok: false, error: error.message }
    }
  }

  /**
   * Resume execution
   * FE-P1-012: Sync execution status with store and state
   * @returns {Promise<Object>} Resume result
   */
  async function resumeExecution() {
    if (!currentExecutionId.value || !canResume.value) {
      return { ok: false, error: 'Cannot resume' }
    }

    try {
      const result = await executionAPI.resumeExecution(currentExecutionId.value)
      if (result.ok) {
        executionStatus.value = 'running'
        isExecuting.value = true
        controlStore.updateStatus('running')
        // Restart polling to track resumed execution
        startExecutionPolling()
      }
      return result
    } catch (error) {
      return { ok: false, error: error.message }
    }
  }

  /**
   * Step execution (execute one node then pause)
   * @returns {Promise<Object>} Step result
   */
  async function stepExecution() {
    if (!currentExecutionId.value || !canStep.value) {
      return { ok: false, error: 'Cannot step' }
    }

    try {
      const result = await executionAPI.stepExecution(currentExecutionId.value)
      return result
    } catch (error) {
      return { ok: false, error: error.message }
    }
  }

  /**
   * Run to end - resume execution and ignore all checkpoints
   * FE-P1-012: Sync execution status with store and state
   * @returns {Promise<Object>} Run to end result
   */
  async function runToEndExecution() {
    if (!currentExecutionId.value || !canResume.value) {
      return { ok: false, error: 'Cannot run to end' }
    }

    try {
      const result = await runToEndAPI(currentExecutionId.value)
      if (result.ok) {
        executionStatus.value = 'running'
        isExecuting.value = true
        controlStore.updateStatus('running')
        // Restart polling to track resumed execution
        startExecutionPolling()
      }
      return result
    } catch (error) {
      return { ok: false, error: error.message }
    }
  }

  /**
   * Resume from checkpoint after failure
   * @param {string} checkpointId - Checkpoint ID to resume from
   * @returns {Promise<Object>} Resume result
   */
  async function resumeFromCheckpoint(checkpointId) {
    if (!currentExecutionId.value) {
      return { ok: false, error: 'No execution to resume' }
    }

    try {
      const result = await controlStore.resumeFromCheckpoint(checkpointId)
      if (result.ok && result.newExecutionId) {
        currentExecutionId.value = result.newExecutionId
        executionStatus.value = 'running'
        isExecuting.value = true
        startExecutionPolling()
      }
      return result
    } catch (error) {
      return { ok: false, error: error.message }
    }
  }

  return {
    stopExecution,
    pauseExecution,
    resumeExecution,
    stepExecution,
    runToEndExecution,
    resumeFromCheckpoint
  }
}
