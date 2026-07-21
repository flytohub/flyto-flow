/**
 * Replay Panel State Composable
 *
 * Manages the UI state for the replay panel.
 */

import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { History, Settings, Search, GitCompare } from 'lucide-vue-next'

export function useReplayPanelState() {
  const { t } = useI18n()

  // Tab configuration
  const tabs = computed(() => [
    { id: 'setup', label: t('common.settings'), icon: Settings },
    { id: 'inspect', label: t('replayMode.inspect'), icon: Search },
    { id: 'history', label: t('replayMode.history'), icon: History },
    { id: 'compare', label: t('replayMode.compare'), icon: GitCompare }
  ])

  // UI State
  const activeTab = ref('setup')
  const replayMode = ref('full') // 'full' or 'step'
  const selectedStepId = ref('')
  const showContextEditor = ref(false)
  const contextOverridesJson = ref('{}')
  const jsonError = ref('')
  const validationResult = ref(null)
  const inspectedStep = ref(null)

  // Execution steps from API
  const executionSteps = ref([])
  const isLoadingSteps = ref(false)
  const contextKeys = ref([])

  // Action states
  const isValidating = ref(false)
  const isStartingReplay = ref(false)
  const actionMessage = ref(null)

  // Validate JSON when it changes
  watch(contextOverridesJson, (json) => {
    try {
      JSON.parse(json)
      jsonError.value = ''
    } catch (e) {
      jsonError.value = 'Invalid JSON format'
    }
  })

  /**
   * Show action message with auto-dismiss
   */
  function showMessage(text, type = 'success') {
    actionMessage.value = { text, type }
    setTimeout(() => {
      actionMessage.value = null
    }, 4000)
  }

  /**
   * Inspect a step (show in drawer)
   */
  function inspectStep(step) {
    inspectedStep.value = step
  }

  /**
   * Select a step for replay from the inspector
   */
  function selectStepForReplay(step) {
    replayMode.value = 'step'
    selectedStepId.value = step.stepId
    inspectedStep.value = null
    activeTab.value = 'setup'
  }

  /**
   * Reset panel state
   */
  function resetState() {
    activeTab.value = 'setup'
    replayMode.value = 'full'
    selectedStepId.value = ''
    showContextEditor.value = false
    contextOverridesJson.value = '{}'
    jsonError.value = ''
    validationResult.value = null
    inspectedStep.value = null
    actionMessage.value = null
  }

  return {
    // Config
    tabs,
    // State
    activeTab,
    replayMode,
    selectedStepId,
    showContextEditor,
    contextOverridesJson,
    jsonError,
    validationResult,
    inspectedStep,
    executionSteps,
    isLoadingSteps,
    contextKeys,
    isValidating,
    isStartingReplay,
    actionMessage,
    // Methods
    showMessage,
    inspectStep,
    selectStepForReplay,
    resetState
  }
}
