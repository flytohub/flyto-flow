/**
 * Execution Control Store Core
 *
 * S-Grade: Core execution control (pause/resume/step).
 * Uses split stores for checkpoints and node outputs.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as executionAPI from '@/api/executions'
import { useCheckpointStore } from './checkpointStore'
import { useNodeOutputStore } from './nodeOutputStore'

export const useExecutionControlStore = defineStore('executionControl', () => {
  // ========== Child Stores ==========
  const checkpointStore = useCheckpointStore()
  const nodeOutputStore = useNodeOutputStore()

  // ========== State ==========
  const executionId = ref(null)
  const status = ref('idle') // idle, running, paused, stepping, paused_at_checkpoint
  const currentState = ref(null)
  const resumeOptions = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // ========== Getters ==========
  const isPaused = computed(() => status.value === 'paused')
  const isRunning = computed(() => status.value === 'running')
  const isStepping = computed(() => status.value === 'stepping')
  const isPausedAtCheckpoint = computed(() => status.value === 'paused_at_checkpoint')
  const canPause = computed(() => status.value === 'running')
  const canResume = computed(() => status.value === 'paused' || status.value === 'paused_at_checkpoint')
  const canStep = computed(() => status.value === 'paused')

  const hasResumeOptions = computed(() => resumeOptions.value?.canResume === true)
  const checkpoints = computed(() => resumeOptions.value?.checkpoints || [])
  const recommendedCheckpoint = computed(() => resumeOptions.value?.recommendedCheckpoint || null)

  const failureInfo = computed(() => {
    if (!resumeOptions.value) return null
    return {
      node: resumeOptions.value.failureNode,
      message: resumeOptions.value.failureMessage
    }
  })

  // ========== Actions ==========

  function setExecution(id, initialStatus = 'running') {
    executionId.value = id
    status.value = initialStatus
    currentState.value = null
    resumeOptions.value = null
    error.value = null
  }

  async function pause(reason = 'user_request') {
    if (!executionId.value || !canPause.value) return false

    loading.value = true
    error.value = null

    try {
      const result = await executionAPI.pauseExecution(executionId.value, reason)
      if (result.ok) {
        status.value = 'paused'
        await fetchState()
      }
      return result.ok
    } catch (err) {
      error.value = err.userMessage || err.message
      return false
    } finally {
      loading.value = false
    }
  }

  async function resume() {
    if (!executionId.value || !canResume.value) return false

    loading.value = true
    error.value = null

    try {
      const result = await executionAPI.resumeExecution(executionId.value)
      if (result.ok) {
        status.value = 'running'
      }
      return result.ok
    } catch (err) {
      error.value = err.userMessage || err.message
      return false
    } finally {
      loading.value = false
    }
  }

  async function step() {
    if (!executionId.value || !canStep.value) return false

    loading.value = true
    error.value = null
    status.value = 'stepping'

    try {
      const result = await executionAPI.stepExecution(executionId.value)
      if (result.ok) {
        status.value = 'paused'
        await fetchState()
      }
      return result.ok
    } catch (err) {
      error.value = err.userMessage || err.message
      status.value = 'paused'
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchState() {
    if (!executionId.value) return null

    loading.value = true

    try {
      const result = await executionAPI.getExecutionState(executionId.value)

      if (result?.ok) {
        currentState.value = result
        nodeOutputStore.updateFromState(result.variables)
        if (result.nodeOutputs) {
          Object.entries(result.nodeOutputs).forEach(([nodeId, output]) => {
            if (!nodeOutputStore.hasOutput(nodeId)) {
              nodeOutputStore.setNodeOutput(nodeId, { output, status: 'completed' })
            }
          })
        }
      }
      return result
    } catch (err) {
      error.value = err.userMessage || err.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchResumeOptions() {
    if (!executionId.value) return null

    loading.value = true

    try {
      const result = await executionAPI.getResumeOptions(executionId.value)
      if (result.ok) {
        resumeOptions.value = result.options || result
      }
      return resumeOptions.value
    } catch (err) {
      error.value = err.userMessage || err.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function resumeFromCheckpoint(checkpointId, modifiedVariables = null) {
    if (!executionId.value) return null

    loading.value = true
    error.value = null

    try {
      const result = await executionAPI.resumeFromCheckpoint(
        executionId.value,
        checkpointId,
        modifiedVariables
      )
      if (result.ok && result.newExecutionId) {
        executionId.value = result.newExecutionId
        status.value = 'running'
        resumeOptions.value = null
        currentState.value = null
      }
      return result
    } catch (err) {
      error.value = err.userMessage || err.message
      return { ok: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  function updateStatus(newStatus) {
    status.value = newStatus
  }

  function clearError() {
    error.value = null
  }

  // ========== Human Checkpoint Actions (delegated) ==========

  function setHumanCheckpoint(checkpointData) {
    checkpointStore.setHumanCheckpoint(checkpointData)
    status.value = 'paused_at_checkpoint'
  }

  async function continueFromCheckpoint() {
    if (!isPausedAtCheckpoint.value) return false
    const result = await checkpointStore.continueFromCheckpoint(executionId.value)
    if (result) status.value = 'running'
    return result
  }

  async function bypassCheckpoint(scope = 'this_run') {
    if (!isPausedAtCheckpoint.value) return false
    const result = await checkpointStore.bypassCheckpoint(executionId.value, scope)
    if (result) status.value = 'running'
    return result
  }

  function reset() {
    executionId.value = null
    status.value = 'idle'
    currentState.value = null
    resumeOptions.value = null
    loading.value = false
    error.value = null
    checkpointStore.reset()
    nodeOutputStore.reset()
  }

  return {
    // State
    executionId,
    status,
    currentState,
    resumeOptions,
    loading,
    error,

    // Exposed from child stores
    nodeOutputs: nodeOutputStore.nodeOutputs,
    humanCheckpoint: checkpointStore.humanCheckpoint,
    bypassedCheckpoints: checkpointStore.bypassedCheckpoints,

    // Getters
    isPaused,
    isRunning,
    isStepping,
    isPausedAtCheckpoint,
    canPause,
    canResume,
    canStep,
    hasResumeOptions,
    checkpoints,
    recommendedCheckpoint,
    failureInfo,
    hasActiveCheckpoint: checkpointStore.hasActiveCheckpoint,
    checkpointProgress: checkpointStore.checkpointProgress,

    // Actions
    setExecution,
    pause,
    resume,
    step,
    fetchState,
    fetchResumeOptions,
    resumeFromCheckpoint,
    updateStatus,
    clearError,

    // Node Output Actions
    getNodeOutput: nodeOutputStore.getNodeOutput,
    clearNodeOutputs: nodeOutputStore.clearAllOutputs,

    // Human Checkpoint Actions
    setHumanCheckpoint,
    continueFromCheckpoint,
    bypassCheckpoint,
    isCheckpointBypassed: checkpointStore.isCheckpointBypassed,
    clearBypassedCheckpoints: checkpointStore.clearBypassedCheckpoints,

    reset
  }
})
