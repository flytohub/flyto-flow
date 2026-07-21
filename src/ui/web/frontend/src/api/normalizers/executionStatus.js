/**
 * Execution Status Normalizer
 *
 * Normalizes backend execution status responses for frontend consumption.
 * S-Grade: All computation done by backend, frontend just uses values directly.
 */

/**
 * @typedef {Object} ProgressInfo
 * @property {number} current - Current step index
 * @property {number} total - Total number of steps
 * @property {number} percent - Progress percentage (0-100) from backend
 */

/**
 * @typedef {Object} NodeTiming
 * @property {string|null} startedAt - ISO timestamp when node started
 * @property {string|null} completedAt - ISO timestamp when node completed
 * @property {number|null} durationMs - Execution duration in milliseconds
 */

/**
 * @typedef {Object} NormalizedExecutionStatus
 * @property {boolean} ok - Whether the request was successful
 * @property {string|null} executionId - Execution identifier
 * @property {string} status - Execution status: 'pending'|'running'|'paused'|'completed'|'failed'|'cancelled'
 * @property {Object.<string, string>|null} nodeStates - Map of nodeId to state ('pending'|'running'|'completed'|'failed')
 * @property {Object.<string, NodeTiming>|null} nodeTimings - Map of nodeId to timing info
 * @property {Object.<string, any>|null} nodeInputs - Map of nodeId to input params (for diff view)
 * @property {Object.<string, any>|null} nodeOutputs - Map of nodeId to output data (for diff view)
 * @property {string|null} activeNodeId - Currently executing node ID
 * @property {Array<string>} completedNodeIds - List of completed node IDs
 * @property {ProgressInfo} progress - Progress information (computed by backend)
 * @property {Object|null} result - Execution result (when completed)
 * @property {string|null} error - Error message (when failed)
 * @property {string|null} errorStepId - Step ID where error occurred
 */

/**
 * Normalize nodeTimings nested keys from snake_case to camelCase
 * Backend returns: { started_at, completed_at, duration_ms }
 * Frontend expects: { startedAt, completedAt, durationMs }
 *
 * @param {Object|null} timings - Raw node timings from backend
 * @returns {Object|null} Normalized timings with camelCase keys
 */
function normalizeNodeTimings(timings) {
  if (!timings) return null

  const normalized = {}
  Object.entries(timings).forEach(([nodeId, timing]) => {
    if (!timing) {
      normalized[nodeId] = null
      return
    }
    normalized[nodeId] = {
      startedAt: timing.started_at ?? timing.startedAt ?? null,
      completedAt: timing.completed_at ?? timing.completedAt ?? null,
      durationMs: timing.duration_ms ?? timing.durationMs ?? null
    }
  })
  return normalized
}

/**
 * Normalize execution status response from backend
 *
 * @param {Object} response - Raw API response
 * @returns {NormalizedExecutionStatus}
 */
export function normalizeExecutionStatus(response) {
  // Handle error responses
  if (!response || !response.ok || !response.execution) {
    return {
      ok: false,
      executionId: null,
      status: 'unknown',
      nodeStates: null,
      nodeTimings: null,
      nodeInputs: null,
      nodeOutputs: null,
      activeNodeId: null,
      completedNodeIds: [],
      progress: { current: 0, total: 0, percent: 0 },
      result: null,
      error: response?.error || 'Failed to fetch execution status',
      errorStepId: null,
      displayOutputs: []
    }
  }

  const exec = response.execution

  // Use backend-computed progress directly (no frontend calculation)
  const progress = exec.progress || {
    current: exec.currentStep || 0,
    total: exec.totalSteps || 0,
    percent: 0
  }

  return {
    ok: true,
    executionId: exec.executionId || exec.execution_id,
    status: exec.status || 'unknown',
    nodeStates: exec.nodeStates || exec.node_states || null,
    nodeTimings: normalizeNodeTimings(exec.nodeTimings || exec.node_timings),
    nodeInputs: exec.nodeInputs || exec.node_inputs || null,
    nodeOutputs: exec.nodeOutputs || exec.node_outputs || null,
    activeNodeId: exec.activeNodeId || exec.active_node_id || null,
    completedNodeIds: exec.completedNodeIds || exec.completed_node_ids || [],
    progress,
    result: exec.result || null,
    error: exec.error || null,
    errorStepId: exec.errorStepId || exec.error_step_id || null,
    displayOutputs: exec.displayOutputs || exec.display_outputs || [],
    hasBrowser: exec.hasBrowser || exec.has_browser || false
  }
}
