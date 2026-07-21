/**
 * Workflows Store - Split Modules Re-exports
 *
 * S-Grade: Centralized exports for workflows functionality.
 *
 * Split structure:
 * - workflowApiActions.js: CRUD operations (~170 lines)
 * - workflowExecutionActions.js: Execution ops (~95 lines)
 * - workflowStoreCore.js: Main store (~80 lines)
 */

// Main store
export { useWorkflowStore } from './workflowStoreCore'

// Action factories for advanced use
export { createWorkflowApiActions } from './workflowApiActions'
export { createWorkflowExecutionActions } from './workflowExecutionActions'
