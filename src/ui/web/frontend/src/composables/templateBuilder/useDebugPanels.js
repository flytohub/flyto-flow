/**
 * Debug Panels Composable
 *
 * Handles debug panel state and interactions.
 */

import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useModulesStore } from '@/stores/modulesStore'
import { resolveModuleLabel } from '@/utils/moduleIdUtils'

export function useDebugPanels({
  debugMode,
  currentExecutionId,
  elements,
  onWorkflowNodeClick,
  showToast
}) {
  const { t } = useI18n()
  const modulesStore = useModulesStore()

  // Active debug panel state
  const activeDebugPanel = ref(null)
  const testStatus = ref(null)
  const lockedVersionCount = ref(0)
  const executionCount = ref(0)

  // Show debug toolbar when execution has completed or is in debug mode
  const showDebugToolbar = computed(() => {
    return debugMode.value || currentExecutionId.value !== null
  })

  // List of modules used in the workflow
  const usedModules = computed(() => {
    const modules = []
    elements.value.forEach(el => {
      if (el.type === 'custom' && el.data?.module) {
        modules.push({
          id: el.data.module,
          name: resolveModuleLabel(el.data.module, modulesStore)
        })
      }
    })
    return modules
  })

  // Workflow steps for replay panel
  const workflowSteps = computed(() => {
    return elements.value
      .filter(el => el.type === 'custom')
      .map(el => ({
        id: el.id,
        name: resolveModuleLabel(el.data?.module, modulesStore) || el.id,
        module: el.data?.module
      }))
  })

  /**
   * Toggle debug panel visibility
   */
  function handleToggleDebugPanel(panel) {
    if (activeDebugPanel.value === panel) {
      activeDebugPanel.value = null
    } else {
      activeDebugPanel.value = panel
    }
  }

  /**
   * Handle lineage node selection
   */
  function handleLineageNodeSelect(node) {
    // Find and select the corresponding workflow node
    const workflowNode = elements.value.find(el => el.id === node.stepId)
    if (workflowNode) {
      onWorkflowNodeClick(workflowNode)
    }
  }

  /**
   * Handle replay started event
   */
  function handleReplayStarted({ replayId }) {
    showToast(t('debug.replay.started'), 'success')
    currentExecutionId.value = replayId
  }

  /**
   * Handle tests completed event
   */
  function handleTestsCompleted({ passed }) {
    testStatus.value = passed ? 'passed' : 'failed'
    showToast(
      passed ? t('debug.tests.allPassed') : t('debug.tests.someFailed'),
      passed ? 'success' : 'error'
    )
  }

  /**
   * Handle version lock changed event
   */
  function handleVersionLockChanged({ locks }) {
    lockedVersionCount.value = Object.keys(locks).length
  }

  return {
    // State
    activeDebugPanel,
    testStatus,
    lockedVersionCount,
    executionCount,
    showDebugToolbar,
    usedModules,
    workflowSteps,
    // Methods
    handleToggleDebugPanel,
    handleLineageNodeSelect,
    handleReplayStarted,
    handleTestsCompleted,
    handleVersionLockChanged
  }
}
