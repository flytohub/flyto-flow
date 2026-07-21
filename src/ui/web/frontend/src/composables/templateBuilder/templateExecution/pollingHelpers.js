/**
 * Polling Helper Functions
 *
 * Pure functions extracted from createPollingActions to reduce complexity.
 * Each function takes explicit parameters instead of relying on closure scope.
 */

import { useToast } from '@/composables/useToast'

/**
 * Update reactive execution state from poll response data
 * @param {Object} state - Reactive state refs
 * @param {Object} data - Poll response data
 * @param {Object} nodeOutputStore - Node output store instance
 * @param {string} pollingMode - 'execution' or 'job'
 */
export function applyPollData(state, data, nodeOutputStore, pollingMode) {
  const {
    executionNodeStates,
    executionNodeTimings,
    executionNodeInputs,
    executionNodeOutputs,
    executionActiveNodeId,
    executionCompletedNodeIds,
    executionProgress,
    executionDisplayOutputs,
    executionStatus,
    hasBrowser
  } = state

  executionNodeStates.value = data.nodeStates || {}
  executionNodeTimings.value = data.nodeTimings || {}
  executionNodeInputs.value = data.nodeInputs || {}
  executionNodeOutputs.value = data.nodeOutputs || {}
  executionActiveNodeId.value = data.activeNodeId
  executionCompletedNodeIds.value = data.completedNodeIds || []
  executionProgress.value = data.progress || { current: 0, total: 0, percent: 0 }
  executionDisplayOutputs.value = data.displayOutputs || []
  // Update hasBrowser from backend data (set by browser_available WebSocket or poll response)
  if (data.hasBrowser !== undefined) {
    hasBrowser.value = !!data.hasBrowser
  }
  nodeOutputStore.updateDisplayOutputsFromList(data.displayOutputs || [])
  if (executionStatus.value !== data.status) {
    executionStatus.value = data.status
  }
}

/**
 * Sync nodeOutputStore with timing/state data from backend
 * @param {Object} nodeOutputStore - Node output store instance
 * @param {Object} data - Poll response data
 */
export function syncNodeOutputStore(nodeOutputStore, data) {
  if (data.nodeTimings) {
    Object.entries(data.nodeTimings).forEach(([nodeId, timing]) => {
      if (timing && timing.durationMs !== null && timing.durationMs !== undefined) {
        const existingOutput = nodeOutputStore.getNodeOutputInfo(nodeId)
        nodeOutputStore.setNodeOutput(nodeId, {
          output: data.nodeOutputs?.[nodeId] ?? existingOutput?.output ?? null,
          status: data.nodeStates?.[nodeId] ?? existingOutput?.status ?? 'completed',
          durationMs: timing.durationMs,
          startedAt: timing.startedAt,
          inputs: data.nodeInputs?.[nodeId] ?? existingOutput?.inputs ?? null,
          error: existingOutput?.error ?? null
        })
      }
    })
  }
  // Fallback: populate from nodeStates for nodes not covered by nodeTimings
  if (data.nodeStates) {
    Object.entries(data.nodeStates).forEach(([nodeId, nodeState]) => {
      if ((nodeState === 'completed' || nodeState === 'failed') && !nodeOutputStore.hasOutput(nodeId)) {
        const timing = data.nodeTimings?.[nodeId]
        nodeOutputStore.setNodeOutput(nodeId, {
          output: data.nodeOutputs?.[nodeId] ?? null,
          status: nodeState,
          durationMs: timing?.durationMs ?? null,
          startedAt: timing?.startedAt ?? null,
          inputs: data.nodeInputs?.[nodeId] ?? null,
          error: nodeState === 'failed' ? (data.error || 'Step failed') : null
        })
      }
    })
  }
}

/**
 * Handle terminal execution statuses (completed/failed/cancelled/paused).
 * Returns a result object if terminal, or null to continue polling.
 * @param {Object} state - Reactive state refs
 * @param {Object} controlStore - Execution control store
 * @param {Object} data - Poll response data
 * @param {string} pollingMode - 'execution' or 'job'
 * @param {Function} stopPollingFn - Function to stop polling
 * @returns {Object|null} Result object if terminal, null otherwise
 */
export function handleTerminalStatus(state, controlStore, data, pollingMode, stopPollingFn) {
  const { executionActiveNodeId, isExecuting, hasBrowser, currentExecutionId, executionStatus } = state

  if (data.status === 'completed') {
    executionActiveNodeId.value = null
    isExecuting.value = false
    if (pollingMode === 'job') hasBrowser.value = false
    stopPollingFn()
    controlStore.setExecution(currentExecutionId.value, 'completed')
    controlStore.fetchState()
    return { status: 'completed' }
  }
  if (data.status === 'failed') {
    executionActiveNodeId.value = null
    isExecuting.value = false
    if (pollingMode === 'job') hasBrowser.value = false
    stopPollingFn()
    controlStore.setExecution(currentExecutionId.value, 'failed')
    controlStore.fetchState()
    controlStore.fetchResumeOptions()
    const toast = useToast()
    toast.error(data.error || 'Workflow execution failed')
    return { status: 'failed', error: data.error }
  }
  if (data.status === 'cancelled') {
    executionActiveNodeId.value = null
    isExecuting.value = false
    if (pollingMode === 'job') hasBrowser.value = false
    stopPollingFn()
    return { status: 'cancelled' }
  }
  if (data.status === 'paused') {
    if (executionStatus.value !== 'paused') {
      controlStore.setExecution(currentExecutionId.value, 'paused')
      controlStore.fetchState()
    }
  }
  return null
}

/**
 * Handle poll error with exponential backoff
 * @param {Object} errorState - Mutable error tracking state
 * @param {Object} config - Polling configuration constants
 * @param {number|undefined} httpStatus - HTTP status code from error
 * @param {Function} resetFn - Function to reset execution state
 * @param {Function} scheduleNextFn - Function to schedule next poll
 */
export function handlePollError(errorState, config, httpStatus, resetFn, scheduleNextFn) {
  errorState.pollErrorCount++
  errorState.currentPollInterval = Math.min(
    errorState.currentPollInterval * config.BACKOFF_MULTIPLIER,
    config.MAX_POLL_INTERVAL_MS
  )
  if (httpStatus === 404 || errorState.pollErrorCount >= config.MAX_POLL_ERRORS) {
    resetFn()
  } else {
    scheduleNextFn()
  }
}
