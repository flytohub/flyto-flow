import { ref, computed, watch } from 'vue'
import { trackBuilder, trackEvidence, trackSession } from '@/utils/telemetryTracker'
import * as executionAPI from '@/api/executions'
import { rerunFromNode } from '@/api/executions'

export function useBuilderSession({
  elements,
  existingTemplateId,
  currentExecutionId,
  isExecuting,
  executionStatus,
  controlStore,
  startExecutionPolling,
  screenshotMode,
  activeDebugPanel,
  builderStore,
  showToast,
  t
}) {
  const executionHistory = ref([])
  const isLoadingHistory = ref(false)

  const sessionStartTime = ref(Date.now())
  const testRunCount = ref(0)
  const sessionId = ref(`session_${Date.now()}`)

  // Track screenshot mode changes
  watch(screenshotMode, (newMode, oldMode) => {
    if (oldMode !== undefined && newMode !== oldMode) {
      trackEvidence.screenshotModeChange(oldMode, newMode, existingTemplateId.value || null)
    }
  })

  // Track test runs (count execution starts)
  watch(isExecuting, (executing, wasExecuting) => {
    if (executing && !wasExecuting) {
      testRunCount.value++
    }
  })

  function handleSelectExecution(execution) {
    currentExecutionId.value = execution.id
    showToast(t('executionHistory.selected', { id: execution.id.slice(0, 8) }), 'info')
  }

  function handleReplayExecution(execution) {
    // Handled via handleReplayStarted in debug panels
    return { replayId: execution.id }
  }

  async function handleStopExecution(execution) {
    showToast(t('executionHistory.stopping'), 'info')

    try {
      const result = await executionAPI.cancelExecution(execution.id)
      if (result.ok) {
        showToast(t('executionHistory.stopped', 'Execution stopped'), 'success')
      } else {
        showToast(result.error || t('executionHistory.stopFailed', 'Failed to stop execution'), 'error')
      }
    } catch (err) {
      console.error('Stop execution failed:', err)
      showToast(t('executionHistory.stopFailed', 'Failed to stop execution'), 'error')
    }
  }

  async function handleRetryFromNode({ nodeId }) {
    if (!currentExecutionId.value) {
      showToast(t('execution.noExecutionToRetry', 'No execution to retry from'), 'warning')
      return
    }

    showToast(t('execution.retryingFromNode', 'Retrying from this node...'), 'info')

    try {
      const result = await rerunFromNode(currentExecutionId.value, nodeId, 'rehydrate')

      if (result.ok && result.newExecutionId) {
        currentExecutionId.value = result.newExecutionId
        isExecuting.value = true
        executionStatus.value = 'running'
        controlStore.setExecution(result.newExecutionId, 'running')

        startExecutionPolling()

        showToast(t('execution.retryStarted', 'Retry started from node'), 'success')
      } else {
        showToast(result.error || t('execution.retryFailed', 'Failed to retry from node'), 'error')
      }
    } catch (err) {
      console.error('Retry from node failed:', err)
      showToast(t('execution.retryFailed', 'Failed to retry from node'), 'error')
    }
  }

  function calculateSessionQuality(edits, testRuns, nodes, durationMs) {
    const minutesActive = durationMs / 60000
    if (minutesActive < 1) return 10

    let score = 0
    score += Math.min(edits * 5, 30)
    score += Math.min(testRuns * 15, 30)
    score += Math.min(nodes * 5, 30)
    score += Math.min(minutesActive * 2, 10)

    return Math.min(Math.round(score), 100)
  }

  function trackSessionStart(templateIdParam) {
    trackBuilder.sessionStart(templateIdParam || null)
  }

  function trackSessionEnd() {
    trackBuilder.sessionEnd(existingTemplateId.value)

    const durationMs = Date.now() - sessionStartTime.value
    const nodeCount = elements.value.filter(el => el.id && !el.source && !el.target).length
    const editCount = builderStore.undoStack?.length || 0

    if (durationMs > 10000) {
      trackSession.quality(sessionId.value, {
        templateId: existingTemplateId.value,
        editCount,
        testRuns: testRunCount.value,
        nodeCount,
        durationMs,
        qualityScore: calculateSessionQuality(editCount, testRunCount.value, nodeCount, durationMs),
      })
    }
  }

  return {
    executionHistory,
    isLoadingHistory,
    sessionStartTime,
    testRunCount,
    sessionId,
    handleSelectExecution,
    handleReplayExecution,
    handleStopExecution,
    handleRetryFromNode,
    trackSessionStart,
    trackSessionEnd
  }
}
