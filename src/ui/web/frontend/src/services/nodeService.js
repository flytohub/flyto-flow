/**
 * Node Service - Unified Node Control Logic
 *
 * Design: Backend is single source of truth.
 * - Backend provides: nodeType, uiConfig, inputHandles, outputHandles, dynamicHandles, defaultParams
 * - Frontend only renders what backend provides, with zero computation/fallback
 *
 * This file provides:
 * - Node type detection (getType) - reads from backend metadata
 * - Vue component resolution (getComponent) - uses nodeComponentRegistry
 * - UI flag access (resolve) - returns backend data directly
 * - Type check utilities (isBranch, isLoop, etc.)
 *
 * IMPORTANT:
 * - paramsComponent is from backend (node_config.py), loaded via ParamsComponentRegistry.js
 * - defaultParams is from backend, used directly by useNodeAddition.js
 * - No TYPE_CONFIGS duplication - removed in favor of backend data
 *
 * Usage:
 *   import { nodeService } from '@/services/nodeService'
 *   const type = nodeService.getType(moduleId, modulesStore)
 *   const config = nodeService.resolve(moduleId, params, modulesStore)
 *   const Component = nodeService.getComponent(moduleId, modulesStore)
 */

import { getNodeComponent as getComponentFromRegistry } from '@/config/nodeComponentRegistry'

// ============================================
// Core Service Functions
// ============================================

/**
 * Get node type from API metadata (source of truth)
 *
 * Backend is the single source of truth for nodeType.
 * The backend detect_node_type() handles all pattern matching.
 * Frontend only uses metadata.nodeType.
 *
 * @param {string} moduleId - Module ID
 * @param {object} modulesStore - Pinia modules store
 * @returns {string} Node type
 */
function getType(moduleId, modulesStore = null) {
  if (!moduleId) return 'standard'
  const metadata = modulesStore?.modulesMetadata?.[moduleId]
  return metadata?.nodeType || 'standard'
}

/**
 * Get UI config from API metadata
 * @param {string} moduleId - Module ID
 * @param {object} modulesStore - Pinia modules store
 * @returns {object} UI config
 */
function getUiConfig(moduleId, modulesStore = null) {
  if (!moduleId) return {}
  const metadata = modulesStore?.modulesMetadata?.[moduleId]
  return metadata?.uiConfig || {}
}

/**
 * Get input handles from API metadata
 * @param {string} moduleId - Module ID
 * @param {object} modulesStore - Pinia modules store
 * @returns {Array} Input handles
 */
function getInputHandles(moduleId, modulesStore = null) {
  if (!moduleId) return []
  const metadata = modulesStore?.modulesMetadata?.[moduleId]
  return metadata?.inputHandles || []
}

/**
 * Get output handles from API metadata
 * @param {string} moduleId - Module ID
 * @param {object} modulesStore - Pinia modules store
 * @returns {Array} Output handles
 */
function getOutputHandles(moduleId, modulesStore = null) {
  if (!moduleId) return []
  const metadata = modulesStore?.modulesMetadata?.[moduleId]
  return metadata?.outputHandles || []
}

/**
 * Get dynamic handles config from API metadata
 * @param {string} moduleId - Module ID
 * @param {object} modulesStore - Pinia modules store
 * @returns {object|null} Dynamic handles config
 */
function getDynamicHandlesConfig(moduleId, modulesStore = null) {
  if (!moduleId) return null
  const metadata = modulesStore?.modulesMetadata?.[moduleId]
  return metadata?.dynamicHandles || null
}

/**
 * Compute dynamic output handles from config + params
 *
 * @param {object} config - Dynamic handles config (fromParam, idPrefix, position, colors)
 * @param {object} params - Node params
 * @returns {Array} Computed handle objects [{id, position, color, label}, ...]
 */
function computeDynamicOutputs(config, params) {
  if (!config || !params) return []

  const { fromParam, position, idPrefix, colors } = config
  const paramValue = params[fromParam]

  if (!paramValue) return []

  // Array of objects (e.g., switch cases: [{id, value, label}, ...])
  // Keep raw id (without prefix) — consumers like useNodeCreation add the prefix themselves
  if (Array.isArray(paramValue)) {
    return paramValue.map((item, index) => ({
      id: item.id,
      position: position || 'right',
      color: colors[index % colors.length],
      label: item.label || item.value || `Case ${index + 1}`
    }))
  }

  // Number (e.g., fork branchCount: 3)
  if (typeof paramValue === 'number') {
    const handles = []
    for (let i = 1; i <= paramValue; i++) {
      handles.push({
        id: `${idPrefix}${i}`,
        position: position || 'right',
        color: colors[(i - 1) % colors.length],
        label: `Branch ${i}`
      })
    }
    return handles
  }

  return []
}

/**
 * Resolve complete node configuration
 * Returns backend data directly - zero computation, zero fallback
 *
 * @param {string} moduleId - Module ID
 * @param {object} params - Node params (for dynamic handles from backend)
 * @param {object} modulesStore - Pinia modules store
 * @returns {object} Complete node config
 */
function resolve(moduleId, params = {}, modulesStore = null) {
  const metadata = modulesStore?.modulesMetadata?.[moduleId]

  if (!metadata) {
    // Minimal fallback for modules not yet loaded
    return {
      type: 'standard',
      styleClass: '',
      isFlowControl: false,
      showAddButton: true,
      handles: { inputs: [], outputs: [] }
    }
  }

  const uiConfig = metadata.uiConfig || {}

  // Return backend data directly
  return {
    type: metadata.nodeType || 'standard',
    styleClass: uiConfig.styleClass || '',
    isFlowControl: uiConfig.isFlowControl || false,
    isLoop: uiConfig.isLoop || false,
    isContainer: uiConfig.isContainer || false,
    isMerge: uiConfig.isMerge || false,
    isFork: uiConfig.isFork || false,
    isJoin: uiConfig.isJoin || false,
    isSubflow: uiConfig.isSubflow || false,
    isTrigger: uiConfig.isTrigger || false,
    isStart: uiConfig.isStart || false,
    isEnd: uiConfig.isEnd || false,
    isEntryPoint: uiConfig.isEntryPoint || false,
    isTerminal: uiConfig.isTerminal || false,
    isCode: uiConfig.isCode || false,
    isHttp: uiConfig.isHttp || false,
    isErrorTrigger: uiConfig.isErrorTrigger || false,
    isLLMChain: uiConfig.isLLMChain || false,
    isVectorStore: uiConfig.isVectorStore || false,
    isAgent: uiConfig.isAgent || false,
    showAddButton: uiConfig.showAddButton ?? true,
    showErrorHandle: uiConfig.showErrorHandle || false,
    handles: {
      inputs: metadata.inputHandles || [],
      outputs: metadata.outputHandles || [],
      loopTargets: metadata.loopTargets || [],
      dynamicOutputs: computeDynamicOutputs(metadata.dynamicHandles, params)
    },
    dynamicHandles: metadata.dynamicHandles || null
  }
}

/**
 * Get Vue component for a node
 * Uses nodeComponentRegistry for mapping
 *
 * @param {string} moduleId - Module ID
 * @param {object} modulesStore - Pinia modules store
 * @param {object} data - Node data (for sub-node detection)
 * @returns {Component} Vue component
 */
function getComponent(moduleId, modulesStore = null, data = null) {
  // Check for AI sub-node first
  if (data?.isSubNode || data?.subNodeType) {
    return getComponentFromRegistry('ai_sub')
  }

  const nodeType = getType(moduleId, modulesStore)
  return getComponentFromRegistry(nodeType)
}

/**
 * Get default params for a module
 * Backend provides pre-computed defaultParams
 *
 * @param {string} moduleId - Module ID
 * @param {object} modulesStore - Pinia modules store
 * @returns {object} Default params
 */
function getDefaultParams(moduleId, modulesStore = null) {
  const metadata = modulesStore?.modulesMetadata?.[moduleId]
  return metadata?.defaultParams || {}
}

// ============================================
// Type Check Functions
// ============================================

const FLOW_CONTROL_TYPES = new Set([
  'branch', 'switch', 'loop', 'container', 'merge', 'fork', 'join',
  'subflow', 'trigger', 'start', 'end', 'error_trigger', 'ai_agent'
])

const ENTRY_TYPES = new Set(['trigger', 'start', 'error_trigger'])

// Fallback set — backend provides isMultiOutput in uiConfig when available
const MULTI_OUTPUT_TYPES = new Set(['branch', 'switch', 'loop', 'fork', 'container', 'ai_agent'])

/** Check if module is a branch node */
function isBranch(moduleId, store = null) {
  return getType(moduleId, store) === 'branch'
}

/** Check if module is a switch node */
function isSwitch(moduleId, store = null) {
  return getType(moduleId, store) === 'switch'
}

/** Check if module is a loop node */
function isLoop(moduleId, store = null) {
  return getType(moduleId, store) === 'loop'
}

/** Check if module is a container node */
function isContainer(moduleId, store = null) {
  return getType(moduleId, store) === 'container'
}

/** Check if module is a merge node */
function isMerge(moduleId, store = null) {
  return getType(moduleId, store) === 'merge'
}

/** Check if module is a fork node */
function isFork(moduleId, store = null) {
  return getType(moduleId, store) === 'fork'
}

/** Check if module is a join node */
function isJoin(moduleId, store = null) {
  return getType(moduleId, store) === 'join'
}

/** Check if module is a subflow node */
function isSubflow(moduleId, store = null) {
  return getType(moduleId, store) === 'subflow'
}

/** Check if module is a trigger node */
function isTrigger(moduleId, store = null) {
  return getType(moduleId, store) === 'trigger'
}

/** Check if module is a start node */
function isStart(moduleId, store = null) {
  return getType(moduleId, store) === 'start'
}

/** Check if module is an end node */
function isEnd(moduleId, store = null) {
  return getType(moduleId, store) === 'end'
}

/** Check if module is an error trigger node */
function isErrorTrigger(moduleId, store = null) {
  return getType(moduleId, store) === 'error_trigger'
}

/** Check if module is a code node */
function isCode(moduleId, store = null) {
  return getType(moduleId, store) === 'code'
}

/** Check if module is an HTTP node */
function isHttp(moduleId, store = null) {
  return getType(moduleId, store) === 'http'
}

/** Check if module is an LLM chain node */
function isLLMChain(moduleId, store = null) {
  return getType(moduleId, store) === 'llm_chain'
}

/** Check if module is a vector store node */
function isVectorStore(moduleId, store = null) {
  return getType(moduleId, store) === 'vector_store'
}

/** Check if module is an AI agent node */
function isAIAgent(moduleId, store = null) {
  return getType(moduleId, store) === 'ai_agent'
}

/** Check if module is a flow control node */
function isFlowControl(moduleId, store = null) {
  const uiConfig = getUiConfig(moduleId, store)
  if (uiConfig.isFlowControl !== undefined) {
    return uiConfig.isFlowControl
  }
  return FLOW_CONTROL_TYPES.has(getType(moduleId, store))
}

/** Check if module is an entry point node (trigger, start, or error trigger) */
function isEntryPoint(moduleId, store = null) {
  const uiConfig = getUiConfig(moduleId, store)
  if (uiConfig.isEntryPoint !== undefined) {
    return uiConfig.isEntryPoint
  }
  return ENTRY_TYPES.has(getType(moduleId, store))
}

/** Check if module is a terminal (end) node */
function isTerminal(moduleId, store = null) {
  const uiConfig = getUiConfig(moduleId, store)
  if (uiConfig.isTerminal !== undefined) {
    return uiConfig.isTerminal
  }
  return getType(moduleId, store) === 'end'
}

/** Check if module has multiple output handles */
function isMultiOutput(moduleId, store = null) {
  const uiConfig = getUiConfig(moduleId, store)
  if (uiConfig.isMultiOutput !== undefined) {
    return uiConfig.isMultiOutput
  }
  return MULTI_OUTPUT_TYPES.has(getType(moduleId, store))
}

/** Check if the add-node button should be shown for this module */
function shouldShowAddButton(moduleId, store = null) {
  const uiConfig = getUiConfig(moduleId, store)
  if (uiConfig.showAddButton !== undefined) {
    return uiConfig.showAddButton
  }
  return !isTerminal(moduleId, store)
}

// ============================================
// Exports
// ============================================

export const nodeService = {
  // Core
  getType,
  getUiConfig,
  getInputHandles,
  getOutputHandles,
  getDynamicHandlesConfig,
  resolve,
  getComponent,
  getDefaultParams,

  // Type checks
  isBranch,
  isSwitch,
  isLoop,
  isContainer,
  isMerge,
  isFork,
  isJoin,
  isSubflow,
  isTrigger,
  isStart,
  isEnd,
  isErrorTrigger,
  isCode,
  isHttp,
  isLLMChain,
  isVectorStore,
  isAIAgent,
  isFlowControl,
  isEntryPoint,
  isTerminal,
  isMultiOutput,
  shouldShowAddButton
}

// Named exports for convenience
export {
  getType,
  getUiConfig,
  getInputHandles,
  getOutputHandles,
  getDynamicHandlesConfig,
  resolve,
  getComponent,
  getDefaultParams,
  isBranch,
  isSwitch,
  isLoop,
  isContainer,
  isMerge,
  isFork,
  isJoin,
  isSubflow,
  isTrigger,
  isStart,
  isEnd,
  isErrorTrigger,
  isCode,
  isHttp,
  isLLMChain,
  isVectorStore,
  isAIAgent,
  isFlowControl,
  isEntryPoint,
  isTerminal,
  isMultiOutput,
  shouldShowAddButton
}

// Backward compatibility aliases (DEPRECATED - use main function names instead)
// These will be removed in a future version. Please migrate to the shorter names:
// - getNodeType -> getType
// - isBranchNode -> isBranch
// - isLoopNode -> isLoop
// etc.
export const getNodeType = getType
export const resolveNode = resolve
export const getNodeComponent = getComponent
export const isBranchNode = isBranch
export const isSwitchNode = isSwitch
export const isLoopNode = isLoop
export const isContainerNode = isContainer
export const isMergeNode = isMerge
export const isForkNode = isFork
export const isJoinNode = isJoin
export const isSubflowNode = isSubflow
export const isTriggerNode = isTrigger
export const isStartNode = isStart
export const isEndNode = isEnd
export const isErrorTriggerNode = isErrorTrigger
export const isCodeNode = isCode
export const isHttpNode = isHttp
export const isLLMChainNode = isLLMChain
export const isVectorStoreNode = isVectorStore
export const isAIAgentNode = isAIAgent
export const isFlowControlNode = isFlowControl
export const isEntryPointNode = isEntryPoint
export const isTerminalNode = isTerminal
export const isMultiOutputNode = isMultiOutput

export default nodeService
