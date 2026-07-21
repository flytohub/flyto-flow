/**
 * Start Node - Explicit Workflow Start
 *
 * Marks the beginning of workflow execution.
 * No input ports - this is always the first node.
 *
 * 5-Star: Handles defined in backend node_config.py
 */
export default {
  type: 'start',

  // No configurable parameters
  getDefaultParams: () => ({}),

  // Style
  styleClass: 'start-node',
  isFlowControl: true,

  // Start-specific flag
  isStart: true,

  // Entry point flag
  isEntryPoint: true,

  // No parameter editor needed
  paramsComponent: null,

  // Show add button after start
  showAddButton: true
}
