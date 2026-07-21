/**
 * Error Trigger Node - Entry point for error-handling workflows
 *
 * This node triggers when another workflow fails, allowing users to
 * build error recovery, notification, or logging workflows.
 *
 * 5-Star: Handles defined in backend node_config.py
 */
export default {
  type: 'error-trigger',

  // Default parameters
  getDefaultParams: () => ({
    // Which workflow to monitor for errors (null = any workflow)
    sourceWorkflowId: null,
    // Which error categories to catch (empty = all errors)
    errorCategories: []
  }),

  // Styling
  styleClass: 'error-trigger-node',

  // Node type flags
  isFlowControl: false,
  isTrigger: true,
  isEntryPoint: true,
  isErrorTrigger: true,

  // Use dedicated params editor
  paramsComponent: 'GenericParams',

  // Show add button for chaining
  showAddButton: true
}
