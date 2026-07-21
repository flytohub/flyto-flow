/**
 * Recording Store
 *
 * Manages browser recording sessions — start/stop and compiled workflow result.
 * Desktop-only — guarded by WORKFLOW_RECORDING capability.
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { post } from '@/api/client'
import { asObject, normalizeRecordingStopResponse } from '@/utils/dataBoundary'

export const useRecordingStore = defineStore('recording', () => {
  const isRecording = ref(false)
  const sessionId = ref(null)
  const error = ref(null)
  const compiledSteps = ref(null)
  const workflowResult = ref(null)
  const recordingSummary = ref(null)
  const compileWarnings = ref([])
  const hasCompileWarnings = computed(() => compileWarnings.value.length > 0)

  async function startRecording(startUrl = '') {
    error.value = null
    compiledSteps.value = null
    workflowResult.value = null
    recordingSummary.value = null
    compileWarnings.value = []

    try {
      const res = asObject(await post('/recording/start', { url: startUrl }))
      sessionId.value = res.sessionId || res.session_id || null
      if (!sessionId.value) {
        throw new Error(res.error || 'Recording session was not created')
      }
      isRecording.value = true
    } catch (e) {
      error.value = e.message || 'Failed to start recording'
      throw e
    }
  }

  async function stopRecording() {
    if (!sessionId.value) return

    try {
      const normalized = normalizeRecordingStopResponse(await post('/recording/stop', { session_id: sessionId.value }))
      workflowResult.value = normalized.workflowResult
      recordingSummary.value = normalized.recordingSummary
      compileWarnings.value = normalized.warnings
      if (!normalized.ok) {
        error.value = normalized.error || 'Failed to compile recording'
        compiledSteps.value = null
        return
      }
      compiledSteps.value = normalized.compiledSteps.length > 0 ? normalized.compiledSteps : null
    } catch (e) {
      error.value = e.message || 'Failed to stop recording'
      compiledSteps.value = null
      workflowResult.value = null
      recordingSummary.value = null
      compileWarnings.value = []
    } finally {
      isRecording.value = false
      sessionId.value = null
    }
  }

  function reset() {
    isRecording.value = false
    sessionId.value = null
    error.value = null
    compiledSteps.value = null
    workflowResult.value = null
    recordingSummary.value = null
    compileWarnings.value = []
  }

  return {
    isRecording,
    sessionId,
    error,
    compiledSteps,
    workflowResult,
    recordingSummary,
    compileWarnings,
    hasCompileWarnings,
    startRecording,
    stopRecording,
    reset,
  }
})
