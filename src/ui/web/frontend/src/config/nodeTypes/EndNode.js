/**
 * End Node - Explicit Workflow End
 *
 * Marks the termination of workflow execution.
 * No output ports - this is always the last node.
 * Can map internal variables to workflow output.
 *
 * 5-Star: Handles defined in backend node_config.py
 */
export default {
  type: 'end',

  // Default parameters
  getDefaultParams: () => ({
    outputMapping: {},
    successMessage: ''
  }),

  // Style
  styleClass: 'end-node',
  isFlowControl: true,

  // End-specific flag
  isEnd: true,

  // Terminal node flag
  isTerminal: true,

  // Parameter editor component
  paramsComponent: 'GenericParams',

  // No add button after end - it's terminal
  showAddButton: false
}
