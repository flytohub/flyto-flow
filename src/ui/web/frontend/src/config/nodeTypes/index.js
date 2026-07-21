/**
 * Node Types
 *
 * DEPRECATED: This file is maintained for backward compatibility only.
 * All logic has been moved to @/services/nodeService.js
 *
 * Usage (preferred):
 *   import { nodeService } from '@/services/nodeService'
 *   const config = nodeService.resolve(moduleId, params, modulesStore)
 *
 * Usage (legacy):
 *   import { resolveNode } from '@/config/nodeTypes'
 */

// Node config files (kept for backward compatibility exports)
import StandardNode from './StandardNode'
import BranchNode from './BranchNode'
import SwitchNode from './SwitchNode'
import LoopNode from './LoopNode'
import ContainerNode from './ContainerNode'
import MergeNode from './MergeNode'
import ForkNode from './ForkNode'
import JoinNode from './JoinNode'
import SubflowNode from './SubflowNode'
import TriggerNode from './TriggerNode'
import StartNode from './StartNode'
import EndNode from './EndNode'
import CodeNode from './CodeNode'
import HttpNode from './HttpNode'
import ErrorTriggerNode from './ErrorTriggerNode'
import LLMChainNode from './LLMChainNode'
import VectorStoreNode from './VectorStoreNode'
import AIAgentNode from './AIAgentNode'

// Re-export core functions from nodeService
export {
  resolveNode,
  getNodeType,
  getDefaultParams,

  // Type checks
  isBranchNode,
  isSwitchNode,
  isLoopNode,
  isFlowControlNode,
  isContainerNode,
  isMergeNode,
  isForkNode,
  isJoinNode,
  isSubflowNode,
  isTriggerNode,
  isStartNode,
  isEndNode,
  isEntryPointNode,
  isTerminalNode,
  isCodeNode,
  isHttpNode,
  isErrorTriggerNode,
  isLLMChainNode,
  isVectorStoreNode,
  isAIAgentNode,
  shouldShowAddButton,

  // Service object
  nodeService
} from '@/services/nodeService'

// Alias for backward compatibility
export { resolveNode as getNodeTypeConfig } from '@/services/nodeService'

// Export all node configs (for debugging and backward compatibility)
export const nodeConfigs = {
  StandardNode,
  BranchNode,
  SwitchNode,
  LoopNode,
  ContainerNode,
  MergeNode,
  ForkNode,
  JoinNode,
  SubflowNode,
  TriggerNode,
  StartNode,
  EndNode,
  CodeNode,
  HttpNode,
  ErrorTriggerNode,
  LLMChainNode,
  VectorStoreNode,
  AIAgentNode
}

// Import nodeService for default export
import { nodeService } from '@/services/nodeService'

export default nodeService
