/**
 * Node Props Builder Registry
 * Centralized props generation for each node type
 *
 * Benefits:
 * - Single source of truth for node props
 * - Easy to add new node types
 * - Follows Open/Closed Principle
 * - Type-specific props are encapsulated
 */

import { NODE_TYPES } from './nodeComponentRegistry'
import { getResourceSlotState } from '@/composables/workflowEditor/nodeRules/resourceSlots'

/**
 * Props builder functions for each node type
 * Each builder receives context and returns the props object
 */
const PROPS_BUILDERS = {
  [NODE_TYPES.TRIGGER]: (ctx) => ({
    ...ctx.baseProps,
    label: ctx.getDisplayLabel(),
    triggerType: ctx.data?.params?.trigger_type || 'manual',
    executionState: ctx.data?.executionState || null
  }),

  [NODE_TYPES.SWITCH]: (ctx) => ({
    ...ctx.baseProps,
    label: ctx.getDisplayLabel(),
    hasLoop: ctx.hasLoop,
    icon: ctx.getNodeIcon(),
    cases: ctx.nodeConfig.handles?.dynamicOutputs || [],
    edges: ctx.edges
  }),

  [NODE_TYPES.BRANCH]: (ctx) => ({
    ...ctx.baseProps,
    label: ctx.getDisplayLabel(),
    hasLoop: ctx.hasLoop,
    icon: ctx.getNodeIcon()
  }),

  [NODE_TYPES.LOOP]: (ctx) => ({
    ...ctx.baseProps,
    icon: ctx.getNodeIcon(),
    label: ctx.getDisplayLabel(),
    edges: ctx.edges
  }),

  [NODE_TYPES.CONTAINER]: (ctx) => ({
    ...ctx.baseProps,
    icon: ctx.getNodeIcon(),
    label: ctx.getDisplayLabel()
  }),

  [NODE_TYPES.AI_AGENT]: (ctx) => ({
    ...ctx.baseProps,
    hasLoop: ctx.hasLoop,
    executionState: ctx.data?.executionState || null,
    agentActivity: ctx.data?.agentActivity || null,
    gradient: ctx.getGradient(),
    icon: ctx.getNodeIcon(),
    label: ctx.getDisplayLabel(),
    subtitle: ctx.getNodeSubtitle(),
    status: ctx.data.status,
    statusIcon: ctx.data.status ? ctx.getStatusIcon(ctx.data.status) : null,
    nodeOutput: ctx.nodeOutput,
    isPinned: ctx.isPinned,
    categoryColor: ctx.getCategoryColor(),
    categoryLabel: ctx.getCategoryLabel(),
    addBtnGradient: `linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)`,
    resourceSlots: getResourceSlotState(ctx.id, ctx.edges),
    inputHandles: ctx.nodeConfig.handles?.inputs || []
  }),

  [NODE_TYPES.AI_SUB]: (ctx) => ({
    ...ctx.baseProps,
    hasLoop: ctx.hasLoop,
    executionState: ctx.data?.executionState || null,
    executionDuration: ctx.data?.executionDuration || null,
    gradient: ctx.getGradient(),
    icon: ctx.getNodeIcon(),
    label: ctx.getDisplayLabel(),
    subtitle: ctx.getNodeSubtitle(),
    status: ctx.data.status,
    statusIcon: ctx.data.status ? ctx.getStatusIcon(ctx.data.status) : null,
    nodeOutput: ctx.nodeOutput,
    isPinned: ctx.isPinned,
    categoryColor: ctx.getCategoryColor(),
    categoryLabel: ctx.getCategoryLabel(),
    addBtnGradient: ctx.getAddBtnGradient()
  }),

  // Default/Standard node props
  [NODE_TYPES.DEFAULT]: (ctx) => {
    // Backend provides showErrorHandle via uiConfig (derived from output ports)
    const showErrorHandle = !ctx.isFlowControl && (
      ctx.nodeConfig.showErrorHandle === true ||
      ctx.data?.enableErrorHandle === true
    )

    return {
      ...ctx.baseProps,
      hasLoop: ctx.hasLoop,
      executionState: ctx.data?.executionState || null,
      executionDuration: ctx.data?.executionDuration || null,
      gradient: ctx.getGradient(),
      icon: ctx.getNodeIcon(),
      label: ctx.getDisplayLabel(),
      subtitle: ctx.getNodeSubtitle(),
      isContainer: ctx.nodeConfig.isContainer,
      containerNodeCount: ctx.data?.params?.subflow?.nodes?.length || 0,
      status: ctx.data.status,
      statusIcon: ctx.data.status ? ctx.getStatusIcon(ctx.data.status) : null,
      isFlowControl: ctx.isFlowControl,
      nodeOutput: ctx.nodeOutput,
      isPinned: ctx.isPinned,
      showErrorHandle,
      categoryColor: ctx.getCategoryColor(),
      categoryLabel: ctx.getCategoryLabel(),
      addBtnGradient: ctx.getAddBtnGradient()
    }
  }
}

// Alias standard to default
PROPS_BUILDERS[NODE_TYPES.STANDARD] = PROPS_BUILDERS[NODE_TYPES.DEFAULT]

/**
 * Build props for a specific node type
 * @param {string} detectedType - The detected node type
 * @param {Object} context - Context object with all required data and helpers
 * @returns {Object} Props object for the node component
 */
export function buildNodeProps(detectedType, context) {
  const builder = PROPS_BUILDERS[detectedType] || PROPS_BUILDERS[NODE_TYPES.DEFAULT]
  return builder(context)
}

/**
 * Register a custom props builder for a node type
 * @param {string} type - Node type identifier
 * @param {Function} builder - Builder function (ctx) => props
 */
export function registerPropsBuilder(type, builder) {
  PROPS_BUILDERS[type] = builder
}

/**
 * Create the context object for props builders
 * This is a helper to ensure all builders receive consistent data
 */
export function createPropsContext({
  // Core props
  id,
  data,
  selected,
  isFirst,
  hasLoop,
  hasForwardEdge,
  showAddButton,
  hasCheckpoint,
  nodeOutput,
  isPinned,
  compact,
  nodeConfig,
  isFlowControl,
  edges,
  // Style helpers
  styleHelpers
}) {
  const moduleId = (() => {
    const raw = data?.module || data?.moduleId
    if (!raw) return ''
    if (typeof raw === 'string') return raw
    if (typeof raw === 'object') {
      return raw.moduleId || raw.id || raw.module || ''
    }
    return ''
  })()

  return {
    // Data
    id,
    data,
    moduleId,
    hasLoop,
    nodeOutput,
    isPinned,
    nodeConfig,
    isFlowControl,
    edges: edges || [],

    // Base props (common to all nodes)
    baseProps: {
      id,
      data,
      selected,
      isFirst,
      hasForwardEdge,
      showAddButton,
      hasCheckpoint,
      compact: compact || false,
      validation: data?.validation || null,
      disabled: data?.disabled || false
    },

    // Style helper functions (bound to moduleId)
    getDisplayLabel: () => styleHelpers.getDisplayLabel(moduleId, data?.label),
    getNodeIcon: () => styleHelpers.getNodeIcon(moduleId),
    getGradient: () => styleHelpers.getGradient(moduleId),
    getNodeSubtitle: () => styleHelpers.getNodeSubtitle(data),
    getStatusIcon: (status) => styleHelpers.getStatusIcon(status),
    getCategoryColor: () => styleHelpers.getCategoryColor(moduleId),
    getCategoryLabel: () => styleHelpers.getCategoryLabel(moduleId),
    getAddBtnGradient: () => {
      const color = styleHelpers.getCategoryColor(moduleId)
      return `linear-gradient(135deg, ${color} 0%, ${color}aa 100%)`
    }
  }
}

export default {
  buildNodeProps,
  registerPropsBuilder,
  createPropsContext
}
