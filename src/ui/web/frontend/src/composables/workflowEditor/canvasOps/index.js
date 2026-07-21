/**
 * Canvas Operations Index
 *
 * S-Grade: Re-exports all split canvas operation modules.
 * New code should import specific modules directly.
 */

// Edge utilities
export {
  DEFAULT_EDGE_OPTIONS,
  EDGE_STYLE,
  EDGE_MARKER,
  createEdge,
  filterEdges,
} from './edgeUtils'

// Node utilities
export {
  createNode,
  generateNodeId,
  calculateNewNodePosition,
  filterNodes,
  getNodeCategory,
  isFlowControlNode,
  isLoopOrGotoNode,
} from './nodeUtils'

// Cascade delete
export {
  removeNodeWithEdges,
  removeNodeWithCascade,
} from './cascadeDelete'

// Auto layout
export { useAutoLayout, PRESETS } from './autoLayout'
