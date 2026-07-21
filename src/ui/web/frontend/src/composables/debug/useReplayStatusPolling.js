/**
 * Replay Status Polling Composable
 *
 * Handles polling for replay execution status.
 */

import { ref, computed, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { replayAPI } from '@/api/replay'

export function useReplayStatusPolling({ showMessage }) {
  const { t } = useI18n()
  // Execution status tracking
  const executionStatus = ref(null)
  const currentReplayId = ref(null)
  let statusPollInterval = null

  // Computed for status bar styling
  const executionStatusClass = computed(() => {
    if (executionStatus.value?.isFailed) return 'bg-red-900/10'
    if (executionStatus.value?.isCompleted) return 'bg-emerald-900/20'
    return 'bg-emerald-900/10'
  })

  const executionStatusText = computed(() => {
    if (!executionStatus.value) return t('debug.replay.initializingReplay')
    if (executionStatus.value.isRunning) return t('debug.replay.replayInProgress')
    if (executionStatus.value.isCompleted) return t('debug.replay.replayCompleted')
    if (executionStatus.value.isFailed) return t('error.replayFailed')
    return t('debug.replay.replayInProgress')
  })

  /**
   * Start polling for replay status
   */
  function startStatusPolling(replayId) {
    stopStatusPolling()
    currentReplayId.value = replayId

    // Initial fetch
    pollReplayStatus(replayId)

    // Start interval
    statusPollInterval = setInterval(() => {
      pollReplayStatus(replayId)
    }, 1000)
  }

  /**
   * Stop status polling
   */
  function stopStatusPolling() {
    if (statusPollInterval) {
      clearInterval(statusPollInterval)
      statusPollInterval = null
    }
  }

  /**
   * Poll replay status
   */
  async function pollReplayStatus(replayId) {
    try {
      const status = await replayAPI.getReplayStatus(replayId)
      executionStatus.value = status

      // Stop polling if completed or failed
      if (status.isCompleted || status.isFailed) {
        stopStatusPolling()

        if (status.isCompleted && showMessage) {
          showMessage(t('message.replayCompleted'), 'success')
        } else if (status.isFailed && showMessage) {
          showMessage(`${t('error.replayFailed')}: ${status.error}`, 'error')
        }
      }
    } catch (e) {
    }
  }

  /**
   * Clear execution status
   */
  function clearExecutionStatus() {
    executionStatus.value = null
    currentReplayId.value = null
  }

  /**
   * Handle cancel
   */
  function handleCancel(resetFn) {
    stopStatusPolling()
    executionStatus.value = null
    currentReplayId.value = null
    if (resetFn) resetFn()
  }

  // Cleanup on unmount
  onUnmounted(() => {
    stopStatusPolling()
  })

  return {
    executionStatus,
    currentReplayId,
    executionStatusClass,
    executionStatusText,
    startStatusPolling,
    stopStatusPolling,
    clearExecutionStatus,
    handleCancel
  }
}
