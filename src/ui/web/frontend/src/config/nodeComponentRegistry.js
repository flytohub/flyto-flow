/**
 * Node Component Registry
 *
 * DEPRECATED: This file is maintained for backward compatibility only.
 * All logic has been moved to @/services/nodeService.js
 *
 * Usage (preferred):
 *   import { nodeService } from '@/services/nodeService'
 *   const Component = nodeService.getComponent(moduleId, modulesStore, data)
 *
 * Usage (legacy):
 *   import { getNodeComponent, detectNodeType } from '@/config/nodeComponentRegistry'
 */

import { markRaw } from 'vue'
import {
  DefaultNode,
  SwitchNode,
  BranchNode,
  LoopNode,
  ContainerNode,
  AIAgentNode,
  AISubNode,
  TriggerNode,
  StickyNote
} from '@/components/workflowCanvas/nodes'

import { nodeService } from '@/services/nodeService'

// Component map for backward compatibility
// Use markRaw to prevent Vue from making components reactive (performance optimization)
const NODE_COMPONENT_MAP = {
  'trigger': markRaw(TriggerNode),
  'switch': markRaw(SwitchNode),
  'branch': markRaw(BranchNode),
  'loop': markRaw(LoopNode),
  'container': markRaw(ContainerNode),
  'ai-agent': markRaw(AIAgentNode),
  'ai_agent': markRaw(AIAgentNode),
  'ai-sub': markRaw(AISubNode),
  'ai_sub': markRaw(AISubNode),
  'sticky': markRaw(StickyNote),
  'sticky-note': markRaw(StickyNote),
  'sticky_note': markRaw(StickyNote),
  'standard': markRaw(DefaultNode),
  'default': markRaw(DefaultNode)
}

/**
 * Get the Vue component for a given node type
 * @param {string} nodeType - The node type identifier
 * @returns {Component} Vue component for the node
 */
export function getNodeComponent(nodeType) {
  return NODE_COMPONENT_MAP[nodeType] || NODE_COMPONENT_MAP['default']
}

/**
 * Detect the effective node type
 * @deprecated Use nodeService.getType() instead
 */
export function detectNodeType(configType, moduleId, data) {
  // AI sub-node detection
  if (data?.isSubNode || data?.subNodeType) {
    return 'ai-sub'
  }

  // Use nodeService for type detection
  // Note: This requires modulesStore to be passed through configType
  // For backward compatibility, we still support direct type strings
  if (configType && typeof configType === 'string') {
    return configType
  }

  return 'default'
}

/**
 * Get component by module
 * @deprecated Use nodeService.getComponent() instead
 */
export function getNodeComponentByModule(configType, moduleId, data) {
  const detectedType = detectNodeType(configType, moduleId, data)
  return getNodeComponent(detectedType)
}

/**
 * Register a new node type and component
 * Automatically wraps component with markRaw for performance
 */
export function registerNodeComponent(type, component) {
  NODE_COMPONENT_MAP[type] = markRaw(component)
}

/**
 * Get all registered node types
 */
export function getRegisteredTypes() {
  return Object.keys(NODE_COMPONENT_MAP)
}

// Type constants
export const NODE_TYPES = {
  TRIGGER: 'trigger',
  SWITCH: 'switch',
  BRANCH: 'branch',
  LOOP: 'loop',
  CONTAINER: 'container',
  AI_AGENT: 'ai_agent',
  AI_SUB: 'ai_sub',
  STICKY: 'sticky',
  STANDARD: 'standard',
  DEFAULT: 'default'
}

export default {
  getNodeComponent,
  detectNodeType,
  getNodeComponentByModule,
  registerNodeComponent,
  getRegisteredTypes,
  NODE_TYPES
}
