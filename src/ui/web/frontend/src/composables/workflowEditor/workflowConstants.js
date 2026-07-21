/**
 * Workflow Constants
 *
 * Re-export layer for backward compatibility.
 * All constants split into workflowConstants/* directory.
 *
 * Split modules:
 * - workflowConstants/handleIds.js: Handle/port ID constants
 * - workflowConstants/edgeConstants.js: Edge types, prefixes, styles, workflow defaults
 * - workflowConstants/idGenerators.js: ID generation utilities
 * - workflowConstants/validators.js: Element validation
 *
 * Layout constants: Use '@/config/nodeDesignSystem' directly
 */

// Re-export all from split modules
export {
  // Module type functions (from nodeTypeRegistry via workflowConstants/index)
  isLoopModule,
  isBranchModule,
  isSwitchModule,
  isFlowControlModule,
  isAIAgentModule,
  isContainerModule,
  isMultiOutputModule,

  // Handle IDs
  HANDLE_IDS,

  // Edge constants
  EDGE_TYPES,
  EDGE_PREFIXES,
  CONNECTION_PORTS,
  EDGE_STYLES,
  DEFAULTS,
  getEmptyConnections,
  isLoopEdge,
  getEdgeColorForSourceHandle,
  applyEdgeVisuals,

  // ID generators
  getRandomSuffix,
  generateNodeId,
  generateEdgeId,

  // Validators
  validateElements,
  separateElements
} from './workflowConstants/index'
