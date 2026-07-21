/**
 * useReplay Composable
 * Manages execution replay state and operations
 */

import { ref, computed, onUnmounted } from 'vue'
import { replayAPI } from '@/api/replay'
import i18n from '@/i18n'
import { telemetry } from '@/services/telemetry'

export function useReplay(options = {}) {
  const { onError, onSuccess, pollInterval = 1000 } = options

  // State
  const replayId = ref(null)
  const replayStatus = ref('idle') // idle, running, completed, failed
  const replayResult = ref(null)
  const comparison = ref(null)
  const replayHistory = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  let pollTimer = null
  let isMounted = true

  // Computed
  const isReplaying = computed(() => replayStatus.value === 'running')
  const canReplay = computed(() => replayStatus.value === 'idle' || replayStatus.value === 'completed')
  const isCompleted = computed(() => replayStatus.value === 'completed')
  const isFailed = computed(() => replayStatus.value === 'failed')

  const hasDifferences = computed(() => {
    if (!comparison.value) return false
    return comparison.value.differences?.length > 0
  })

  // Actions
  async function validateReplay(executionId, fromStepId) {
    try {
      const data = await replayAPI.validateReplay(executionId, fromStepId)
      return { ok: data.canReplay, data }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  async function startReplay(executionId, config = {}) {
    isLoading.value = true
    error.value = null
    replayStatus.value = 'running'

    // Track replay start
    telemetry.track('replay.start', {
      execution_id: executionId,
      from_step: config.from_step_id
    })

    try {
      const data = await replayAPI.startReplay(executionId, config)
      if (data.ok || data.replayId) {
        replayId.value = data.replayId
        startPolling(data.replayId)
        onSuccess?.('replay_started')
        return { ok: true, replayId: data.replayId }
      }
      throw new Error(data.error || i18n.global.t('error.replayFailedToStart'))
    } catch (err) {
      error.value = err.message || err.userMessage || 'Replay failed'
      replayStatus.value = 'failed'

      // Track replay error
      telemetry.track('replay.error', {
        execution_id: executionId,
        error: error.value
      })

      onError?.(err)
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function replayStep(executionId, stepId, contextOverrides = {}) {
    isLoading.value = true
    error.value = null

    // Track step replay
    telemetry.track('replay.step', {
      execution_id: executionId,
      step_id: stepId,
      has_overrides: Object.keys(contextOverrides).length > 0
    })

    try {
      const data = await replayAPI.replayStep(executionId, stepId, contextOverrides)
      replayResult.value = data
      onSuccess?.('step_replayed')
      return { ok: true, data }
    } catch (err) {
      error.value = err.message || err.userMessage || 'Step replay failed'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function compareExecutions(originalId, replayExecutionId) {
    isLoading.value = true
    error.value = null

    try {
      const data = await replayAPI.compareExecutions(originalId, replayExecutionId)
      comparison.value = data
      return { ok: true, data }
    } catch (err) {
      error.value = err.message || err.userMessage || 'Comparison failed'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function loadHistory(executionId) {
    try {
      const data = await replayAPI.getReplayHistory(executionId)
      replayHistory.value = data.history || []
      return { ok: true, data: replayHistory.value }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  async function cancelReplay() {
    if (!replayId.value) return { ok: false, error: 'No active replay' }

    try {
      await replayAPI.cancelReplay(replayId.value)
      stopPolling()
      replayStatus.value = 'idle'
      return { ok: true }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  function startPolling(id) {
    stopPolling()
    pollTimer = setInterval(async () => {
      if (!isMounted) {
        stopPolling()
        return
      }
      try {
        const status = await replayAPI.getReplayStatus(id)
        if (status.completed) {
          replayStatus.value = 'completed'
          replayResult.value = status.result
          stopPolling()
          onSuccess?.('replay_completed')
        } else if (status.failed) {
          replayStatus.value = 'failed'
          error.value = status.error || 'Replay failed'
          stopPolling()
          onError?.(new Error(error.value))
        }
      } catch (e) {
        // Continue polling on error
      }
    }, pollInterval)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function reset() {
    stopPolling()
    replayId.value = null
    replayStatus.value = 'idle'
    replayResult.value = null
    comparison.value = null
    error.value = null
  }

  onUnmounted(() => {
    isMounted = false
    stopPolling()
  })

  return {
    // State
    replayId,
    replayStatus,
    replayResult,
    comparison,
    replayHistory,
    isLoading,
    error,

    // Computed
    isReplaying,
    canReplay,
    isCompleted,
    isFailed,
    hasDifferences,

    // Actions
    validateReplay,
    startReplay,
    replayStep,
    compareExecutions,
    loadHistory,
    cancelReplay,
    reset
  }
}

export default useReplay
