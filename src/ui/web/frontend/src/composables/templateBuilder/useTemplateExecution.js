/**
 * Template Execution Composable
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All execution logic split into templateExecution/* directory.
 *
 * Split modules:
 * - templateExecution/state.js: State and computed creation
 * - templateExecution/pollingActions.js: Polling logic
 * - templateExecution/runWorkflowAction.js: Run workflow action
 * - templateExecution/controlActions.js: Execution control actions
 * - templateExecution/useTemplateExecutionCore.js: Main composable
 */

// Re-export from split modules
export { useTemplateExecution } from './templateExecution'

// Re-export utilities for advanced use
export {
  createExecutionState,
  createExecutionComputed,
  createDebugActions,
  createPollingActions,
  createRunWorkflowAction,
  createControlActions
} from './templateExecution'
