/**
 * Recording WebSocket Composable
 *
 * Handles WebSocket connection for browser recording.
 */

import { ref, onUnmounted } from 'vue'

export function useRecordingWebSocket({
  isRecording,
  isPaused,
  recordingDuration,
  recordedActions,
  selectedAction,
  options,
  showStatus,
  addAction,
  emit
}) {
  const recordingSocket = ref(null)
  const durationInterval = ref(null)

  /**
   * Start recording session
   */
  async function startRecording(targetUrl) {
    if (!targetUrl) {
      showStatus('Please enter a target URL', 'error')
      return
    }

    try {
      isRecording.value = true
      recordingDuration.value = 0
      recordedActions.value = []

      // Start duration timer
      durationInterval.value = setInterval(() => {
        if (!isPaused.value) {
          recordingDuration.value++
        }
      }, 1000)

      // Connect to recording backend
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/recording/ws`
      recordingSocket.value = new WebSocket(wsUrl)

      recordingSocket.value.onopen = () => {
        recordingSocket.value.send(JSON.stringify({
          type: 'start',
          url: targetUrl,
          options: options.value
        }))
        showStatus('Recording started', 'success')
      }

      recordingSocket.value.onmessage = (event) => {
        const data = JSON.parse(event.data)
        handleRecordingMessage(data)
      }

      recordingSocket.value.onerror = (error) => {
        showStatus('Recording connection error', 'error')
        stopRecording()
      }

      recordingSocket.value.onclose = () => {
        if (isRecording.value) {
          stopRecording()
        }
      }

    } catch (error) {
      showStatus(`Failed to start recording: ${error.message}`, 'error')
      isRecording.value = false
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  function handleRecordingMessage(data) {
    switch (data.type) {
      case 'action':
        addAction(data.action)
        break
      case 'screenshot':
        // Handle screenshot data
        if (selectedAction.value !== null) {
          recordedActions.value[selectedAction.value].screenshot = data.data
        }
        break
      case 'error':
        showStatus(data.message, 'error')
        break
      case 'status':
        showStatus(data.message, 'info')
        break
    }
  }

  /**
   * Stop recording session
   */
  function stopRecording() {
    isRecording.value = false
    isPaused.value = false

    if (durationInterval.value) {
      clearInterval(durationInterval.value)
      durationInterval.value = null
    }

    if (recordingSocket.value) {
      recordingSocket.value.send(JSON.stringify({ type: 'stop' }))
      recordingSocket.value.close()
      recordingSocket.value = null
    }

    showStatus(`Recording complete: ${recordedActions.value.length} actions`, 'success')
    if (emit) emit('recording-complete', recordedActions.value)
  }

  /**
   * Toggle pause/resume
   */
  function togglePause() {
    isPaused.value = !isPaused.value
    if (recordingSocket.value) {
      recordingSocket.value.send(JSON.stringify({
        type: isPaused.value ? 'pause' : 'resume'
      }))
    }
  }

  /**
   * Cleanup on unmount
   */
  function cleanup() {
    if (durationInterval.value) {
      clearInterval(durationInterval.value)
    }
    if (recordingSocket.value) {
      recordingSocket.value.close()
    }
  }

  // Auto cleanup on unmount
  onUnmounted(cleanup)

  return {
    recordingSocket,
    startRecording,
    stopRecording,
    togglePause,
    cleanup
  }
}
