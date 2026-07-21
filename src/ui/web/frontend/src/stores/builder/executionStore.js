/**
 * Builder Execution Store
 * Manages execution state, debug mode, and preview results
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { telemetry } from '@/services/telemetry'

export const useBuilderExecutionStore = defineStore('builder-execution', () => {
  // ========== Debug State ==========
  const debugMode = ref(false)
  const debugSelectedNodeIds = ref([])

  // ========== Execution State ==========
  const isExecuting = ref(false)
  const executionCurrentStep = ref(null)
  const executionCompletedSteps = ref([])

  // ========== Preview Execution State ==========
  const previewExecutionResult = ref(null)
  const previewExecutionError = ref(null)

  // ========== Debug Actions ==========
  function toggleDebugMode() {
    debugMode.value = !debugMode.value

    // Track debug mode toggle
    telemetry.track('debug.toggle', {
      enabled: debugMode.value
    })

    return debugMode.value
  }

  function setDebugMode(enabled) {
    debugMode.value = enabled
  }

  function setDebugSelectedNodes(nodeIds) {
    debugSelectedNodeIds.value = nodeIds
  }

  function clearDebugSelection() {
    debugSelectedNodeIds.value = []
  }

  // ========== Execution Actions ==========
  function startExecution() {
    isExecuting.value = true
    executionCurrentStep.value = null
    executionCompletedSteps.value = []
  }

  function setExecutionStep(step) {
    executionCurrentStep.value = step
  }

  function completeExecutionStep(stepId) {
    if (!executionCompletedSteps.value.includes(stepId)) {
      executionCompletedSteps.value.push(stepId)
    }
  }

  function stopExecution() {
    isExecuting.value = false
  }

  function resetExecution() {
    isExecuting.value = false
    executionCurrentStep.value = null
    executionCompletedSteps.value = []
  }

  // ========== Preview Execution Actions ==========
  function setPreviewResult(result) {
    previewExecutionResult.value = result
  }

  function setPreviewError(error) {
    previewExecutionError.value = error
  }

  function clearPreviewState() {
    previewExecutionResult.value = null
    previewExecutionError.value = null
  }

  // ========== Reset ==========
  function reset() {
    debugMode.value = false
    debugSelectedNodeIds.value = []
    resetExecution()
    clearPreviewState()
  }

  return {
    // Debug State
    debugMode,
    debugSelectedNodeIds,

    // Execution State
    isExecuting,
    executionCurrentStep,
    executionCompletedSteps,

    // Preview Execution State
    previewExecutionResult,
    previewExecutionError,

    // Debug Actions
    toggleDebugMode,
    setDebugMode,
    setDebugSelectedNodes,
    clearDebugSelection,

    // Execution Actions
    startExecution,
    setExecutionStep,
    completeExecutionStep,
    stopExecution,
    resetExecution,

    // Preview Execution Actions
    setPreviewResult,
    setPreviewError,
    clearPreviewState,

    // Reset
    reset
  }
})
