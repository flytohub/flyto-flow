/**
 * Node Type Registry
 *
 * DEPRECATED: This file is maintained for backward compatibility only.
 * All logic has been moved to @/services/nodeService.js
 *
 * Usage (preferred):
 *   import { nodeService } from '@/services/nodeService'
 *
 * Usage (legacy):
 *   import { getNodeType, isBranchNode } from '@/config/nodeTypeRegistry'
 */

export {
  // Core functions
  getNodeType,
  getUiConfig,
  getInputHandles,
  getOutputHandles,
  getDynamicHandlesConfig,

  // Type checks
  isBranchNode,
  isSwitchNode,
  isLoopNode,
  isContainerNode,
  isMergeNode,
  isForkNode,
  isJoinNode,
  isSubflowNode,
  isTriggerNode,
  isStartNode,
  isEndNode,
  isErrorTriggerNode,
  isCodeNode,
  isHttpNode,
  isLLMChainNode,
  isVectorStoreNode,
  isAIAgentNode,
  isFlowControlNode,
  isEntryPointNode,
  isTerminalNode,
  isMultiOutputNode,
  shouldShowAddButton,

  // Service object
  nodeService as default
} from '@/services/nodeService'

// Feature flag re-export
import { USE_API_NODE_CONFIG as _USE_API_NODE_CONFIG } from '@/config/featureFlags'
export const USE_API_NODE_CONFIG = _USE_API_NODE_CONFIG

// Alias for getParamsComponent
export { getUiConfig as getParamsComponent } from '@/services/nodeService'

// Alias for getStyleClass
export { getUiConfig as getStyleClass } from '@/services/nodeService'
