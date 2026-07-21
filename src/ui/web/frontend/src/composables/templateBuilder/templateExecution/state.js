/**
 * Template Execution State
 *
 * S-Grade: State creation for template execution.
 * Single responsibility: State and computed definitions.
 */

import { ref, computed } from 'vue'

/**
 * Create initial state for template execution
 * @returns {Object} State refs
 */
export function createExecutionState() {
  // Execution state
  const isExecuting = ref(false)
  const currentExecutionId = ref(null)
  const executionStatus = ref('idle') // idle, running, paused, completed, failed

  // Backend-computed states (S-Grade: no frontend computation)
  const executionNodeStates = ref({})
  const executionNodeTimings = ref({})  // { nodeId: { startedAt, completedAt, durationMs } }
  const executionNodeInputs = ref({})   // { nodeId: inputParams } for diff view
  const executionNodeOutputs = ref({})  // { nodeId: outputData } for diff view
  const executionActiveNodeId = ref(null)
  const executionCompletedNodeIds = ref([])
  const executionProgress = ref({ current: 0, total: 0, percent: 0 })

  // Display outputs (collected from __display__: true results)
  const executionDisplayOutputs = ref([])

  // Debug mode state
  const debugMode = ref(false)
  const debugSelectedNodeIds = ref([])

  // Screenshot mode: 'off' | 'on_error' | 'all'
  const screenshotMode = ref('on_error')

  // Browser screencast availability
  const hasBrowser = ref(false)

  // Agent real-time activity: { [stepId]: { tool, iteration, type } }
  const agentActivity = ref({})

  return {
    isExecuting,
    currentExecutionId,
    executionStatus,
    executionNodeStates,
    executionNodeTimings,
    executionNodeInputs,
    executionNodeOutputs,
    executionActiveNodeId,
    executionCompletedNodeIds,
    executionProgress,
    executionDisplayOutputs,
    debugMode,
    debugSelectedNodeIds,
    screenshotMode,
    hasBrowser,
    agentActivity
  }
}

/**
 * Create computed properties for execution
 * @param {Object} state - State refs
 * @returns {Object} Computed properties
 */
export function createExecutionComputed(state) {
  const { executionStatus } = state

  const isPaused = computed(() => executionStatus.value === 'paused')
  const canPause = computed(() => executionStatus.value === 'running')
  const canResume = computed(() => executionStatus.value === 'paused')
  const canStep = computed(() => executionStatus.value === 'paused')

  return {
    isPaused,
    canPause,
    canResume,
    canStep
  }
}

/**
 * Create debug mode actions
 * @param {Object} state - State refs
 * @returns {Object} Debug actions
 */
export function createDebugActions(state) {
  const { debugMode, debugSelectedNodeIds } = state

  /**
   * Toggle debug mode
   */
  function toggleDebugMode() {
    if (debugMode.value) {
      debugMode.value = false
      debugSelectedNodeIds.value = []
    } else {
      debugMode.value = true
    }
    return debugMode.value
  }

  /**
   * Handle debug selection change from canvas
   * @param {Array<string>} selectedIds - Selected node IDs
   */
  function onDebugSelectionChange(selectedIds) {
    debugSelectedNodeIds.value = selectedIds
  }

  return {
    toggleDebugMode,
    onDebugSelectionChange
  }
}
