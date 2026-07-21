/**
 * Container Node - Embedded Subflow Container
 *
 * Click to open new Tab for editing nested workflow.
 * Supports max 5 levels of nesting.
 *
 * 5-Star: Handles defined in backend node_config.py
 */
export default {
  type: 'container',

  // Default parameters
  getDefaultParams: () => ({
    subflow: {
      nodes: [],
      edges: []
    },
    inheritContext: true,
    isolatedVariables: [],
    exportVariables: []
  }),

  // Style
  styleClass: 'container-node',
  isFlowControl: true,

  // Container-specific flag
  isContainer: true,

  // Parameter editor component
  paramsComponent: 'GenericParams',

  // Show add button after container
  showAddButton: true,

  // Helper to get node count inside container
  getNodeCount: (params) => {
    return params?.subflow?.nodes?.length || 0
  },

  // Helper to check if container is empty
  isEmpty: (params) => {
    const nodes = params?.subflow?.nodes || []
    return nodes.length === 0
  }
}
