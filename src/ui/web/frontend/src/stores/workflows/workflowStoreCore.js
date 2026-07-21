/**
 * Workflow Store Core
 *
 * S-Grade: Main workflow store using extracted actions.
 * Manages workflow state and operations.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createWorkflowApiActions } from './workflowApiActions'
import { createWorkflowExecutionActions } from './workflowExecutionActions'

export const useWorkflowStore = defineStore('workflow', () => {
  // ========== State ==========
  const workflows = ref([])
  const currentWorkflow = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  // Execution state
  const executionStatus = ref(null)
  const executionLogs = ref([])
  const executionProgress = ref(0)

  // Backend-computed counts
  const enabledCount = ref(0)
  const totalCount = ref(0)

  // ========== Getters ==========
  const hasWorkflows = computed(() => workflows.value.length > 0)
  const getWorkflowById = computed(() => (id) => workflows.value.find(w => w.id === id))
  const isExecuting = computed(() => executionStatus.value === 'running')

  // ========== State refs for actions ==========
  const state = {
    workflows, currentWorkflow, isLoading, error,
    executionStatus, executionLogs, executionProgress,
    enabledCount, totalCount
  }

  // ========== Actions ==========
  const apiActions = createWorkflowApiActions(state)
  const execActions = createWorkflowExecutionActions(state)

  function setCurrentWorkflow(workflow) {
    currentWorkflow.value = workflow
  }

  function clearError() {
    error.value = null
  }

  function reset() {
    workflows.value = []
    currentWorkflow.value = null
    isLoading.value = false
    error.value = null
    enabledCount.value = 0
    totalCount.value = 0
    execActions.resetExecutionState()
  }

  return {
    // State
    workflows, currentWorkflow, isLoading, error,
    executionStatus, executionLogs, executionProgress,
    enabledCount, totalCount,
    // Getters
    hasWorkflows, getWorkflowById, isExecuting,
    // API Actions
    ...apiActions,
    // Execution Actions
    ...execActions,
    // Utility
    setCurrentWorkflow, clearError, reset
  }
})
