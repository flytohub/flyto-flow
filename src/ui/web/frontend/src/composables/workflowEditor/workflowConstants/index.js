/**
 * Workflow Constants - Split Exports
 *
 * S-Grade: Centralized exports for workflow constants.
 *
 * Split structure:
 * - handleIds.js: Handle/port ID constants
 * - edgeConstants.js: Edge types, prefixes, styles, workflow defaults
 * - idGenerators.js: ID generation utilities
 * - validators.js: Element validation
 *
 * Layout constants: Use '@/config/nodeDesignSystem' directly
 *
 * Module type checks: Use '@/services/nodeService' directly
 */

// Module type functions - re-export from nodeService for backward compatibility
export {
  isLoopNode as isLoopModule,
  isBranchNode as isBranchModule,
  isSwitchNode as isSwitchModule,
  isFlowControlNode as isFlowControlModule,
  isAIAgentNode as isAIAgentModule,
  isContainerNode as isContainerModule,
  isMultiOutputNode as isMultiOutputModule
} from '@/services/nodeService'

// Handle IDs
export { HANDLE_IDS } from './handleIds'

// Edge constants + workflow defaults
export {
  EDGE_TYPES,
  EDGE_PREFIXES,
  CONNECTION_PORTS,
  EDGE_STYLES,
  DEFAULTS,
  getEmptyConnections,
  isLoopEdge,
  getEdgeColorForSourceHandle,
  applyEdgeVisuals
} from './edgeConstants'

// ID generators
export {
  getRandomSuffix,
  generateNodeId,
  generateEdgeId
} from './idGenerators'

// Validators
export {
  validateElements,
  separateElements
} from './validators'
