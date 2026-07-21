/**
 * Standard Node - General node configuration
 *
 * 5-Star: Handles defined in backend node_config.py
 */
export default {
  type: 'standard',

  // Default parameters
  getDefaultParams: () => ({}),

  // Styling
  styleClass: '',
  isFlowControl: false,

  // Parameter editor component
  paramsComponent: 'GenericParams',

  // Show add button
  showAddButton: true
}
