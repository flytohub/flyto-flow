/**
 * useEvidence Composable
 * Manages step evidence state and operations
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { evidenceAPI } from '@/api/evidence'
import i18n from '@/i18n'

export function useEvidence(options = {}) {
  const { executionId, autoLoad = false, onError } = options

  // State
  const evidences = ref([])
  const selectedEvidence = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  // Computed
  const hasScreenshots = computed(() =>
    evidences.value.some(e => e.screenshotPath)
  )

  const browserSteps = computed(() =>
    evidences.value.filter(e => e.moduleId?.startsWith('browser.'))
  )

  const evidenceCount = computed(() => evidences.value.length)

  const hasEvidence = computed(() => evidences.value.length > 0)

  // Actions
  async function loadEvidences(execId) {
    const id = execId || executionId
    if (!id) return { ok: false, error: 'No execution ID' }

    isLoading.value = true
    error.value = null

    try {
      const data = await evidenceAPI.getExecutionEvidence(id)
      evidences.value = data.steps || []
      return { ok: true, data: evidences.value }
    } catch (err) {
      error.value = err.message || err.userMessage || i18n.global.t('error.failedToLoadEvidence')
      onError?.(err)
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function loadStepEvidence(execId, stepId) {
    isLoading.value = true
    error.value = null

    try {
      const data = await evidenceAPI.getStepEvidence(execId, stepId)
      selectedEvidence.value = data
      return { ok: true, data }
    } catch (err) {
      error.value = err.message || err.userMessage || i18n.global.t('error.failedToLoadStepEvidence')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function loadContextDiff(execId, stepId) {
    try {
      const data = await evidenceAPI.getContextDiff(execId, stepId)
      return { ok: true, data }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  function getScreenshotUrl(execId, stepId) {
    return evidenceAPI.getScreenshotUrl(execId, stepId)
  }

  function getDomUrl(execId, stepId) {
    return evidenceAPI.getDomUrl(execId, stepId)
  }

  function selectEvidence(evidence) {
    selectedEvidence.value = evidence
  }

  function clearSelection() {
    selectedEvidence.value = null
  }

  function reset() {
    evidences.value = []
    selectedEvidence.value = null
    error.value = null
  }

  // Lifecycle
  onMounted(() => {
    if (autoLoad && executionId) {
      loadEvidences()
    }
  })

  onUnmounted(() => {
    selectedEvidence.value = null
  })

  return {
    // State
    evidences,
    selectedEvidence,
    isLoading,
    error,

    // Computed
    hasScreenshots,
    browserSteps,
    evidenceCount,
    hasEvidence,

    // Actions
    loadEvidences,
    loadStepEvidence,
    loadContextDiff,
    getScreenshotUrl,
    getDomUrl,
    selectEvidence,
    clearSelection,
    reset
  }
}

export default useEvidence
