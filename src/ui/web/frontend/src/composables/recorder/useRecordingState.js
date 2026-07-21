/**
 * Recording State Composable
 *
 * Manages the core recording state including actions, selection, and status.
 */

import { ref, computed } from 'vue'

export function useRecordingState() {
  // Core state
  const targetUrl = ref('')
  const isRecording = ref(false)
  const isPaused = ref(false)
  const recordingDuration = ref(0)
  const recordedActions = ref([])
  const selectedAction = ref(null)
  const editingAction = ref({})
  const statusMessage = ref('')
  const statusType = ref('info')

  // Recording options
  const options = ref({
    captureScreenshots: true,
    recordNetwork: false,
    waitForNavigation: true,
    generateAssertions: false,
    selectorStrategy: 'auto'
  })

  /**
   * Show status message
   */
  function showStatus(message, type = 'info') {
    statusMessage.value = message
    statusType.value = type
    setTimeout(() => {
      statusMessage.value = ''
    }, 3000)
  }

  /**
   * Reset recording state
   */
  function resetState() {
    recordingDuration.value = 0
    recordedActions.value = []
    selectedAction.value = null
    editingAction.value = {}
  }

  return {
    // State
    targetUrl,
    isRecording,
    isPaused,
    recordingDuration,
    recordedActions,
    selectedAction,
    editingAction,
    statusMessage,
    statusType,
    options,
    // Methods
    showStatus,
    resetState
  }
}
