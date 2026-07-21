/**
 * Node Rules Module - Split Exports (UX HINTS ONLY)
 *
 * S-Grade: Centralized exports for node behavior rules.
 *
 * IMPORTANT: These rules are UX hints for immediate visual feedback.
 * The authoritative validation is done by the backend via POST /workflows/validate.
 * Frontend rules help users build valid workflows but are NOT authoritative.
 * Always call backend validation before save/execute.
 *
 * Split structure:
 * - handleVisibility.js: Handle visibility rules (~70 lines)
 * - nodeCascade.js: Deletion cascade logic (~85 lines)
 * - loopRules.js: Loop mode rules (~40 lines) - UX hints
 * - branchRules.js: Multi-output rules (~50 lines) - UX hints
 * - connectionValidation.js: Connection validation (~45 lines) - UX hints
 * - resourceSlots.js: AI-agent model/memory/tools resource slot limits
 */

// Handle visibility
export {
  getHandleVisibility,
  isFirstNode,
  isLeafNode
} from './handleVisibility'

// Node cascade
export {
  isLoopBackEdge,
  getNodeDeletionCascade,
  getEdgesAfterNodeDeletion
} from './nodeCascade'

// Loop rules
export {
  hasLoopNodes,
  hasLoopEdges,
  isLoopNode,
  isLoopModule
} from './loopRules'

// Branch rules
export {
  canHaveMultipleOutputs,
  getMaxOutputs,
  hasReachedMaxOutputs
} from './branchRules'

// Connection validation
export { validateConnection } from './connectionValidation'

// AI agent resource slots
export {
  getResourceSlotType,
  getResourceSlotCounts,
  getResourceSlotState,
  canAddResourceToHandle
} from './resourceSlots'
