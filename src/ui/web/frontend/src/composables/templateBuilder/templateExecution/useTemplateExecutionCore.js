/**
 * useTemplateExecution Core Composable
 *
 * S-Grade: Main template execution composable.
 * Single responsibility: Compose and expose execution functionality.
 */

import { onUnmounted } from 'vue'
import { useExecutionControlStore } from '@/stores/executionControlStore'
import { createExecutionState, createExecutionComputed, createDebugActions } from './state'
import { createPollingActions } from './pollingActions'
import { createRunWorkflowAction } from './runWorkflowAction'
import { createControlActions } from './controlActions'

/**
 * Template Execution Composable
 * Handles workflow execution, polling, debug mode, and execution control
 *
 * @returns {Object} Execution state and actions
 */
export function useTemplateExecution() {
  // Execution control store
  const controlStore = useExecutionControlStore()

  // Create state
  const state = createExecutionState()

  // Create computed properties
  const computed = createExecutionComputed(state)

  // Create actions from modules
  const pollingActions = createPollingActions(state, controlStore)
  const debugActions = createDebugActions(state)
  const { runWorkflow } = createRunWorkflowAction(state, pollingActions)
  const controlActions = createControlActions(state, computed, pollingActions, controlStore)

  // Cleanup polling on unmount
  onUnmounted(() => {
    pollingActions.setUnmounted()
  })

  return {
    // State
    isExecuting: state.isExecuting,
    currentExecutionId: state.currentExecutionId,
    executionStatus: state.executionStatus,
    // Backend-computed states (S-Grade)
    executionNodeStates: state.executionNodeStates,
    executionNodeTimings: state.executionNodeTimings,
    executionNodeInputs: state.executionNodeInputs,
    executionNodeOutputs: state.executionNodeOutputs,
    executionActiveNodeId: state.executionActiveNodeId,
    executionCompletedNodeIds: state.executionCompletedNodeIds,
    executionProgress: state.executionProgress,
    executionDisplayOutputs: state.executionDisplayOutputs,
    // Debug mode
    debugMode: state.debugMode,
    debugSelectedNodeIds: state.debugSelectedNodeIds,
    screenshotMode: state.screenshotMode,
    // Browser screencast
    hasBrowser: state.hasBrowser,
    // Agent real-time activity
    agentActivity: state.agentActivity,

    // Computed
    ...computed,

    // Control store access
    controlStore,

    // Debug actions
    ...debugActions,

    // Run workflow
    runWorkflow,

    // Control actions
    ...controlActions,

    // Polling actions (FE-P0-004: expose for retry-from-node)
    startExecutionPolling: pollingActions.startExecutionPolling,
    stopExecutionPolling: pollingActions.stopExecutionPolling,

    // Reset state
    resetExecutionState: pollingActions.resetExecutionState
  }
}
