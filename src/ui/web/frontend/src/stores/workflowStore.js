/**
 * Workflow Store
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All functionality split into stores/workflows/* directory.
 *
 * Split modules:
 * - workflows/workflowApiActions.js: CRUD operations
 * - workflows/workflowExecutionActions.js: Execution operations
 * - workflows/workflowStoreCore.js: Main store
 */

// Re-export store
export { useWorkflowStore } from './workflows'

// Re-export action factories for advanced use
export {
  createWorkflowApiActions,
  createWorkflowExecutionActions
} from './workflows'
