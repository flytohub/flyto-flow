/**
 * Node Rules Composable
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All node rules split into nodeRules/* directory.
 *
 * Split modules:
 * - nodeRules/handleVisibility.js: Handle visibility rules
 * - nodeRules/nodeCascade.js: Deletion cascade logic
 * - nodeRules/loopRules.js: Loop mode rules
 * - nodeRules/branchRules.js: Multi-output rules
 * - nodeRules/connectionValidation.js: Connection validation
 */

// Re-export all from split modules
export {
  // Handle visibility
  getHandleVisibility,
  isFirstNode,
  isLeafNode,

  // Node cascade
  isLoopBackEdge,
  getNodeDeletionCascade,
  getEdgesAfterNodeDeletion,

  // Loop rules
  hasLoopNodes,
  hasLoopEdges,
  isLoopNode,
  isLoopModule,

  // Branch rules
  canHaveMultipleOutputs,
  getMaxOutputs,
  hasReachedMaxOutputs,

  // Connection validation
  validateConnection
} from './nodeRules/index'
