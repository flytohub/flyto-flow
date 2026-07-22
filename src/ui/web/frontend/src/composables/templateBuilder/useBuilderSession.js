import { ref } from 'vue'
import * as executionAPI from '@/api/executions'
import { rerunFromNode } from '@/api/executions'

/** Local execution-history actions with no analytics or session tracking. */
export function useBuilderSession({
  currentExecutionId,
  isExecuting,
  executionStatus,
  controlStore,
  startExecutionPolling,
  showToast,
  t,
}) {
  const executionHistory = ref([])
  const isLoadingHistory = ref(false)

  function handleSelectExecution(execution) {
    currentExecutionId.value = execution.id
    showToast(t('executionHistory.selected', { id: execution.id.slice(0, 8) }), 'info')
  }
  function handleReplayExecution(execution) { return { replayId: execution.id } }
  async function handleStopExecution(execution) {
    showToast(t('executionHistory.stopping'), 'info')
    try {
      const result = await executionAPI.cancelExecution(execution.id)
      showToast(
        result.ok ? t('executionHistory.stopped', 'Execution stopped') : (result.error || t('executionHistory.stopFailed', 'Failed to stop execution')),
        result.ok ? 'success' : 'error',
      )
    } catch (error) {
      console.error('Stop execution failed:', error)
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
      if (!result.ok || !result.newExecutionId) {
        showToast(result.error || t('execution.retryFailed', 'Failed to retry from node'), 'error')
        return
      }
      currentExecutionId.value = result.newExecutionId
      isExecuting.value = true
      executionStatus.value = 'running'
      controlStore.setExecution(result.newExecutionId, 'running')
      startExecutionPolling()
      showToast(t('execution.retryStarted', 'Retry started from node'), 'success')
    } catch (error) {
      console.error('Retry from node failed:', error)
      showToast(t('execution.retryFailed', 'Failed to retry from node'), 'error')
    }
  }

  return {
    executionHistory,
    isLoadingHistory,
    handleSelectExecution,
    handleReplayExecution,
    handleStopExecution,
    handleRetryFromNode,
  }
}
