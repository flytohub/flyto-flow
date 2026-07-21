/**
 * Execution Control API
 * Pause, Resume, Step, and Resume-from-failure operations
 */

import { get, post } from './client'
import { ENDPOINTS } from './config'
import { normalizeExecutionStatus } from './normalizers/executionStatus'

/**
 * Get execution status (with auth)
 * @param {string} executionId - Execution ID
 * @returns {Promise<import('./normalizers/executionStatus').NormalizedExecutionStatus>}
 */
export async function getExecutionStatus(executionId) {
  try {
    const response = await get(ENDPOINTS.EXECUTIONS.GET(executionId))
    return normalizeExecutionStatus(response)
  } catch (err) {
    return normalizeExecutionStatus({ ok: false, error: err.userMessage || err.message })
  }
}

/**
 * Cancel a running execution (with auth)
 * @param {string} executionId - Execution ID
 * @returns {Promise<{ok: boolean, message: string}>}
 */
export async function cancelExecution(executionId) {
  try {
    return await post(`/executions/${executionId}/cancel`)
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Pause a running execution
 * @param {string} executionId - Execution ID
 * @param {string} reason - Pause reason (user_request, breakpoint, error, step_complete)
 * @returns {Promise<{ok: boolean, message: string}>}
 */
export async function pauseExecution(executionId, reason = 'user_request') {
  try {
    return await post(ENDPOINTS.EXECUTIONS.PAUSE(executionId), { reason })
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Resume a paused execution
 * @param {string} executionId - Execution ID
 * @returns {Promise<{ok: boolean, message: string}>}
 */
export async function resumeExecution(executionId) {
  try {
    return await post(ENDPOINTS.EXECUTIONS.RESUME(executionId))
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Execute single step then pause
 * @param {string} executionId - Execution ID
 * @returns {Promise<{ok: boolean, message: string}>}
 */
export async function stepExecution(executionId) {
  try {
    return await post(ENDPOINTS.EXECUTIONS.STEP(executionId))
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Run to end - resume execution and ignore all breakpoints
 * @param {string} executionId - Execution ID
 * @returns {Promise<{ok: boolean, message: string}>}
 */
export async function runToEnd(executionId) {
  try {
    return await post(ENDPOINTS.EXECUTIONS.RUN_TO_END(executionId))
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Get current execution state (variables, outputs)
 * @param {string} executionId - Execution ID
 * @returns {Promise<{ok: boolean, state: Object}>}
 */
export async function getExecutionState(executionId) {
  try {
    return await get(ENDPOINTS.EXECUTIONS.STATE(executionId))
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Get available resume options for a failed execution
 * @param {string} executionId - Execution ID
 * @returns {Promise<{ok: boolean, options: Object}>}
 */
export async function getResumeOptions(executionId) {
  try {
    return await get(ENDPOINTS.EXECUTIONS.RESUME_OPTIONS(executionId))
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Resume execution from a checkpoint
 * @param {string} executionId - Original execution ID
 * @param {string} checkpointId - Checkpoint to resume from
 * @param {Object} modifiedVariables - Optional variable modifications
 * @returns {Promise<{ok: boolean, newExecutionId: string}>}
 */
export async function resumeFromCheckpoint(executionId, checkpointId, modifiedVariables = null) {
  try {
    return await post(ENDPOINTS.EXECUTIONS.RESUME_CHECKPOINT(executionId), {
      checkpointId,
      modifiedVariables
    })
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

// ========== Human Checkpoint API ==========

/**
 * Continue execution from human checkpoint (process next item)
 * @param {string} executionId - Execution ID
 * @returns {Promise<{ok: boolean}>}
 */
export async function continueFromCheckpoint(executionId) {
  try {
    return await post(ENDPOINTS.EXECUTIONS.CONTINUE_CHECKPOINT(executionId))
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Bypass human checkpoint and run all remaining items
 * @param {string} executionId - Execution ID
 * @param {string} checkpointId - Checkpoint ID to bypass
 * @param {string} scope - 'this_run' | 'this_version'
 * @returns {Promise<{ok: boolean}>}
 */
export async function bypassCheckpoint(executionId, checkpointId, scope = 'this_run') {
  try {
    return await post(ENDPOINTS.EXECUTIONS.BYPASS_CHECKPOINT(executionId), {
      checkpointId,
      scope
    })
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

// ========== Debug/Rerun API ==========

/**
 * Rerun execution from a specific node
 * Uses REHYDRATE mode to inject outputs from previous steps
 * @param {string} executionId - Original execution ID
 * @param {string} nodeId - Node ID to start from
 * @param {string} mode - 'rehydrate' (inject previous outputs) | 'recompute' (rerun dependencies)
 * @param {Object} overrideInputs - Optional input overrides
 * @returns {Promise<{ok: boolean, newExecutionId?: string, error?: string}>}
 */
export async function rerunFromNode(executionId, nodeId, mode = 'rehydrate', overrideInputs = null) {
  try {
    const result = await post(ENDPOINTS.DEBUG.RERUN(executionId), {
      node_id: nodeId,
      mode,
      override_inputs: overrideInputs
    })
    return {
      ok: result.success !== false,
      newExecutionId: result.new_execution_id || result.newExecutionId,
      error: result.error
    }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

export default {
  getExecutionStatus,
  cancelExecution,
  pauseExecution,
  resumeExecution,
  stepExecution,
  runToEnd,
  getExecutionState,
  getResumeOptions,
  resumeFromCheckpoint,
  continueFromCheckpoint,
  bypassCheckpoint,
  rerunFromNode
}
