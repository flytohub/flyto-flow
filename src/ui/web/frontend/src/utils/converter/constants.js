/**
 * Converter Constants
 *
 * Module type checks use '@/services/nodeService' as single source of truth.
 * Re-exports with "Module" aliases for backward compatibility.
 */

import {
  isLoopNode,
  isBranchNode,
  isSwitchNode,
  isContainerNode
} from '@/services/nodeService'

// Re-export with "Module" alias for backward compatibility
export const isLoopModule = isLoopNode
export const isBranchModule = isBranchNode
export const isSwitchModule = isSwitchNode
export const isContainerModule = isContainerNode

// Also export with "Node" names (preferred)
export { isLoopNode, isBranchNode, isSwitchNode, isContainerNode }
