/**
 * Execution Polling Actions
 *
 * S-Grade: Polling logic for execution status.
 * Single responsibility: Start/stop/manage polling.
 */

import * as executionAPI from '@/api/executions'
import { useNodeOutputStore } from '@/stores/execution/nodeOutputStore'
import { applyPollData, syncNodeOutputStore, handleTerminalStatus, handlePollError } from './pollingHelpers'
import { connectExecWs, disconnectExecWs } from './pollingWebSocket'

const MAX_POLL_ERRORS = 3
const BASE_POLL_INTERVAL_MS = 500  // Base polling interval (reasonable for UI updates)
const MAX_POLL_INTERVAL_MS = 3000  // Max interval after backoff
const BACKOFF_MULTIPLIER = 1.5    // Exponential backoff multiplier

const POLL_CONFIG = { MAX_POLL_ERRORS, BACKOFF_MULTIPLIER, MAX_POLL_INTERVAL_MS }

/**
 * Create polling actions
 * @param {Object} state - State refs
 * @param {Object} controlStore - Execution control store
 * @returns {Object} Polling actions and state
 */
export function createPollingActions(state, controlStore) {
  const nodeOutputStore = useNodeOutputStore()

  // Polling state
  let pollTimeout = null
  let pollErrorCount = 0
  let isMounted = true
  let isPolling = false
  let pollPromise = null  // FE-P0-005: Track active poll promise for atomic guard
  let currentPollInterval = BASE_POLL_INTERVAL_MS

  // WebSocket ref container (mutable object so helpers can update it)
  const wsRef = { ws: null }

  // --- Internal helpers ---

  function _disconnectWs() {
    disconnectExecWs(wsRef)
  }

  function _handleStepCompleted(msg) {
    // Real-time step output via WebSocket — update nodeOutputStore immediately
    if (msg.step_id && msg.output !== undefined) {
      const nodeOutputStore = useNodeOutputStore()
      nodeOutputStore.setNodeOutput(msg.step_id, msg.output)
    }
    // Track completed node
    if (msg.step_id && !state.executionCompletedNodeIds.value.includes(msg.step_id)) {
      state.executionCompletedNodeIds.value.push(msg.step_id)
    }
    // Clear agent activity when step completes
    if (msg.step_id && state.agentActivity.value[msg.step_id]) {
      const updated = { ...state.agentActivity.value }
      delete updated[msg.step_id]
      state.agentActivity.value = updated
    }
  }

  function _handleAgentEvent(msg) {
    // Real-time agent streaming events via WebSocket
    if (!msg.step_id) return
    if (msg.type === 'agent:tool_call') {
      state.agentActivity.value = {
        ...state.agentActivity.value,
        [msg.step_id]: {
          type: 'tool_call',
          tool: msg.tool,
          iteration: msg.iteration,
          maxIterations: msg.max_iterations,
          toolCallIndex: msg.tool_call_index,
        }
      }
    } else if (msg.type === 'agent:tool_result') {
      // Brief flash of completion before next tool
      if (state.agentActivity.value[msg.step_id]) {
        state.agentActivity.value = {
          ...state.agentActivity.value,
          [msg.step_id]: {
            ...state.agentActivity.value[msg.step_id],
            type: 'tool_result',
            ok: msg.ok,
          }
        }
      }
    } else if (msg.type === 'agent:iteration') {
      state.agentActivity.value = {
        ...state.agentActivity.value,
        [msg.step_id]: {
          ...state.agentActivity.value[msg.step_id],
          type: 'iteration',
          iteration: msg.iteration,
          maxIterations: msg.max_iterations,
        }
      }
    }
  }

  function stopExecutionPolling() {
    if (pollTimeout) {
      clearTimeout(pollTimeout)
      pollTimeout = null
    }
    isPolling = false
    currentPollInterval = BASE_POLL_INTERVAL_MS
    _disconnectWs()
  }

  function resetExecutionState() {
    state.isExecuting.value = false
    state.executionNodeStates.value = {}
    state.executionNodeTimings.value = {}
    state.executionNodeInputs.value = {}
    state.executionNodeOutputs.value = {}
    state.executionActiveNodeId.value = null
    state.executionCompletedNodeIds.value = []
    state.executionProgress.value = { current: 0, total: 0, percent: 0 }
    state.executionDisplayOutputs.value = []
    state.agentActivity.value = {}
    // NOTE: hasBrowser is NOT reset here — it stays true until browser.close
    stopExecutionPolling()
  }

  function scheduleNextPoll() {
    if (!isMounted || !state.currentExecutionId.value) return
    pollTimeout = setTimeout(pollExecution, currentPollInterval)
  }

  // Error state object passed to handlePollError (mutable reference)
  const errorState = {
    get pollErrorCount() { return pollErrorCount },
    set pollErrorCount(v) { pollErrorCount = v },
    get currentPollInterval() { return currentPollInterval },
    set currentPollInterval(v) { currentPollInterval = v }
  }

  /**
   * Internal poll execution logic
   */
  async function doPollExecution() {
    try {
      const data = await executionAPI.getExecutionStatus(state.currentExecutionId.value)
      pollErrorCount = 0
      currentPollInterval = BASE_POLL_INTERVAL_MS

      if (data.ok) {
        applyPollData(state, data, nodeOutputStore, 'execution')
        syncNodeOutputStore(nodeOutputStore, data)
        const result = handleTerminalStatus(state, controlStore, data, 'execution', stopExecutionPolling)
        if (result) return result
        scheduleNextPoll()
      } else {
        handlePollError(errorState, POLL_CONFIG, undefined, resetExecutionState, scheduleNextPoll)
      }
    } catch (error) {
      handlePollError(errorState, POLL_CONFIG, error.response?.status, resetExecutionState, scheduleNextPoll)
    } finally {
      isPolling = false
    }
  }

  /**
   * Single poll execution
   * FE-P0-005: Atomic polling guard using promise tracking
   */
  async function pollExecution() {
    if (!isMounted || !state.currentExecutionId.value) {
      stopExecutionPolling()
      return
    }
    if (pollPromise) return pollPromise
    if (isPolling) {
      scheduleNextPoll()
      return
    }
    isPolling = true
    pollPromise = doPollExecution()
    try {
      return await pollPromise
    } finally {
      pollPromise = null
    }
  }

  // --- Public API ---

  function setUnmounted() {
    stopExecutionPolling()
    isMounted = false
  }

  function startExecutionPolling() {
    stopExecutionPolling()
    pollErrorCount = 0
    currentPollInterval = BASE_POLL_INTERVAL_MS
    state.executionProgress.value = { current: 0, total: 0, percent: 0 }
    state.executionCompletedNodeIds.value = []
    connectExecWs({
      executionId: state.currentExecutionId.value,
      hasBrowser: state.hasBrowser,
      wsRef,
      disconnectFn: _disconnectWs,
      onStepCompleted: _handleStepCompleted,
      onAgentEvent: _handleAgentEvent,
    })
    scheduleNextPoll()
  }

  return {
    startExecutionPolling,
    stopExecutionPolling,
    resetExecutionState,
    setUnmounted
  }
}
