/**
 * Branch Node - Conditional branch node
 * If/Else logic with two output handles: True / False
 *
 * 5-Star: Handles defined in backend node_config.py
 */
export default {
  type: 'branch',

  // Default parameters
  getDefaultParams: () => ({
    condition: ''
  }),

  // Styling
  styleClass: 'branch-node',
  isFlowControl: true,

  // Parameter editor component
  paramsComponent: 'FlowControlParams',

  // Show add button
  showAddButton: true
}
