/**
 * Canvas Operations Composable
 *
 * S-Grade: This file is being deprecated in favor of split modules.
 * New code should import from './canvasOps' instead.
 *
 * Split modules:
 * - canvasOps/edgeUtils.js - Edge creation and utilities
 * - canvasOps/nodeUtils.js - Node creation and utilities
 * - canvasOps/cascadeDelete.js - Node deletion with cascade logic
 * - canvasOps/autoLayout.js - Auto layout system
 */

// Re-export everything from split modules
export {
  // Edge utilities
  DEFAULT_EDGE_OPTIONS,
  EDGE_STYLE,
  EDGE_MARKER,
  createEdge,
  filterEdges,
  // Node utilities
  createNode,
  generateNodeId,
  calculateNewNodePosition,
  filterNodes,
  getNodeCategory,
  isFlowControlNode,
  isLoopOrGotoNode,
  // Cascade delete
  removeNodeWithEdges,
  removeNodeWithCascade,
} from './canvasOps'

// Re-export from workflowConstants for backward compatibility
export { isBranchModule as isBranchNode } from './workflowConstants'
export { isSwitchModule as isSwitchNode } from './workflowConstants'
export { isMultiOutputModule as isMultiOutputNode } from './workflowConstants'
export { isAIAgentModule } from './workflowConstants'
