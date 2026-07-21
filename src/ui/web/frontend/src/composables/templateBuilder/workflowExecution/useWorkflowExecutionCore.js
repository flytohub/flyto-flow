/**
 * Workflow Execution Core
 *
 * S-Grade: Main workflow execution composable.
 * Single responsibility: Compose execution functionality.
 */

import { useI18n } from 'vue-i18n'
import { collectUIInputValues } from './uiInputs'
import { createExecutionControls } from './executionControls'
import { createCheckpointHandlers } from './checkpointHandlers'

export function useWorkflowExecution({
  elements,
  templateId,
  templateName,
  templateData,
  builderStore,
  executeWorkflow,
  stopWorkflowExecution,
  pauseExecution,
  stepExecution,
  resumeExecution,
  runToEndExecution,
  resumeFromCheckpoint,
  controlStore,
  showToast
}) {
  const { t } = useI18n()

  // Create execution controls
  const executionControls = createExecutionControls({
    executeWorkflow,
    stopWorkflowExecution,
    pauseExecution,
    stepExecution,
    resumeExecution,
    runToEndExecution,
    showToast,
    t
  })

  /**
   * Collect UI inputs and run workflow
   * For locked templates (no elements but has templateId), uses direct API execution
   */
  async function runWorkflow() {
    const uiInputValues = collectUIInputValues(templateData)

    // Check if this is a locked template:
    // If we have a templateId but elements array is empty, it's locked
    const elementsArray = elements?.value || elements || []
    const hasTemplateId = !!(templateId?.value || templateId)
    const hasNoElements = elementsArray.length === 0
    const isWorkflowLocked = hasTemplateId && hasNoElements

    return executionControls.runWorkflow({
      elements,
      templateId,
      templateName,
      uiInputValues,
      checkpoints: builderStore.checkpoints,
      isWorkflowLocked
    })
  }

  // Create checkpoint handlers
  const checkpointHandlers = createCheckpointHandlers({
    resumeFromCheckpoint,
    controlStore,
    builderStore,
    showToast,
    t,
    runWorkflow
  })

  return {
    collectUIInputValues: () => collectUIInputValues(templateData),
    runWorkflow,
    stopExecution: executionControls.stopExecution,
    handlePause: executionControls.handlePause,
    handleStep: executionControls.handleStep,
    handleStop: executionControls.handleStop,
    handleResume: executionControls.handleResume,
    handleRunToEnd: executionControls.handleRunToEnd,
    ...checkpointHandlers,
  }
}
