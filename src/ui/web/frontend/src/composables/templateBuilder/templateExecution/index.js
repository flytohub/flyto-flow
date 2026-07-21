/**
 * Template Execution Module - Split Exports
 *
 * S-Grade: Centralized exports for template execution.
 *
 * Split structure:
 * - state.js: State and computed creation (~95 lines)
 * - pollingActions.js: Polling logic (~130 lines)
 * - runWorkflowAction.js: Run workflow action (~105 lines)
 * - controlActions.js: Execution control actions (~150 lines)
 * - useTemplateExecutionCore.js: Main composable (~70 lines)
 */

// Main composable
export { useTemplateExecution } from './useTemplateExecutionCore'

// State factories for advanced use
export { createExecutionState, createExecutionComputed, createDebugActions } from './state'

// Action factories for composition
export { createPollingActions } from './pollingActions'
export { createRunWorkflowAction } from './runWorkflowAction'
export { createControlActions } from './controlActions'
