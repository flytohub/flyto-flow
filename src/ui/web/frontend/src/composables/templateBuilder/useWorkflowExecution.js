/**
 * Workflow Execution Composable
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All workflow execution logic split into workflowExecution/* directory.
 *
 * Split modules:
 * - workflowExecution/uiInputs.js: UI input collection
 * - workflowExecution/executionControls.js: Run, stop, pause, resume
 * - workflowExecution/checkpointHandlers.js: Checkpoint operations
 * - workflowExecution/useWorkflowExecutionCore.js: Main composable
 */

// Re-export all from split modules
export {
  useWorkflowExecution,
  collectUIInputValues,
  FORM_TYPES,
  createExecutionControls,
  createCheckpointHandlers
} from './workflowExecution/index'
