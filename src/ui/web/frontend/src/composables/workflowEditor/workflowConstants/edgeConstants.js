/**
 * Edge Constants
 *
 * S-Grade: Edge type constants and helpers.
 * Single source of truth: '@/services/nodeService'
 */

import { MarkerType } from '@vue-flow/core'
import { nodeService } from '@/services/nodeService'
import { HANDLE_IDS } from './handleIds'
import { DEFAULTS as GLOBAL_DEFAULTS } from '@/config/defaults'

/**
 * Default parameter values for workflow nodes
 */
export const DEFAULTS = {
  LOOP_TIMES: 10,
  TIMEOUT_MS: GLOBAL_DEFAULTS.API.TIMEOUT,
  MAX_RETRIES: GLOBAL_DEFAULTS.RETRY.MAX_RETRIES
}

/**
 * Edge type identifiers
 */
export const EDGE_TYPES = {
  CONTROL: 'control',
  RESOURCE: 'resource',
  LOOP: 'loop'
}

/**
 * Edge ID prefixes
 */
export const EDGE_PREFIXES = {
  NORMAL: 'e_',
  LOOP: 'e_loop_',
  BRANCH_TRUE: 'e_branch_true_',
  BRANCH_FALSE: 'e_branch_false_',
  SWITCH_CASE: 'e_switch_case_',
  SWITCH_DEFAULT: 'e_switch_default_',
  ERROR: 'e_error_'
}

/**
 * V1.2 Connection Ports by flow control type
 * Used to initialize connections for flow control nodes
 */
export const CONNECTION_PORTS = {
  LOOP: {
    iterate: [],  // Target for loop-back
    done: []      // Target when loop completes
  },
  BRANCH: {
    true: [],     // Target when condition is true
    false: []     // Target when condition is false
  },
  SWITCH: {
    default: []   // Default target
  }
}

/**
 * Get empty connections object for a flow control module
 * @param {string} moduleId - The module identifier
 * @param {object} modulesStore - Optional modules store
 * @returns {Object|null} Empty connections object or null if not a flow control module
 */
export function getEmptyConnections(moduleId, modulesStore = null) {
  if (nodeService.isLoop(moduleId, modulesStore)) {
    return { iterate: [], done: [] }
  }
  if (nodeService.isBranch(moduleId, modulesStore)) {
    return { true: [], false: [] }
  }
  if (nodeService.isSwitch(moduleId, modulesStore)) {
    return { default: [] }
  }
  return null
}

/**
 * Default edge styling
 */
export const EDGE_STYLES = {
  NORMAL: {
    stroke: '#8B5CF6',
    strokeWidth: 2
  },
  LOOP: {
    stroke: '#F59E0B',
    strokeWidth: 3
  },
  ERROR: {
    stroke: '#EF4444',
    strokeWidth: 2
  }
}

/**
 * Check if an edge is a loop-back edge
 * Priority: ID prefix > handle name > class
 * Note: 'animated' is NOT used as it's unreliable (non-loop edges can be animated)
 * @param {Object} edge - The edge object
 * @returns {boolean}
 */
export function isLoopEdge(edge) {
  if (!edge) return false
  return (
    edge.id?.startsWith(EDGE_PREFIXES.LOOP) ||
    edge.sourceHandle === 'body_out' ||
    edge.data?.edgeType === 'iterate' ||
    edge.class === 'loop-edge'
  )
}

/**
 * Get edge color for switch case/branch handles
 *
 * Determines edge color based on source handle type:
 * - Branch true: green (#10B981)
 * - Branch false: red (#EF4444)
 * - Switch cases: color from case index
 *
 * @param {string} handle - Source handle ID
 * @param {Object} sourceNode - Source node
 * @param {Array} caseColors - Available case colors
 * @returns {string|null} Color hex code or null
 */
export function getEdgeColorForSourceHandle(handle, sourceNode, caseColors = []) {
  if (!handle || !sourceNode) return null

  // Switch case - get color from case index
  if (handle.includes('source-case-')) {
    const cases = sourceNode.data?.params?.cases || []
    const caseIndex = cases.findIndex(c => handle.includes(c.id))
    if (caseIndex >= 0 && caseColors.length > 0) {
      return caseColors[caseIndex % caseColors.length]
    }
  }

  // Branch true/false
  if (handle === 'source-true') return '#10B981' // green
  if (handle === 'source-false') return '#EF4444' // red

  // Error output
  if (handle === 'source-error' || handle.includes('error')) return '#EF4444' // red

  // Error handler handled/escalate
  if (handle === 'source-handled') return '#10B981' // green
  if (handle === 'source-escalate') return '#F59E0B' // orange

  return null
}

/**
 * Check if an edge is an error routing edge
 * @param {Object} edge - The edge object
 * @returns {boolean}
 */
export function isErrorEdge(edge) {
  if (!edge) return false
  return (
    edge.id?.startsWith(EDGE_PREFIXES.ERROR) ||
    edge.sourceHandle === 'source-error' ||
    edge.sourceHandle?.includes('error') ||
    edge.targetHandle === 'error' ||
    edge.class === 'error-edge'
  )
}

/**
 * Get edge style based on edge type
 * @param {Object} edge - The edge object
 * @returns {Object} Style object
 */
export function getEdgeStyle(edge) {
  if (isLoopEdge(edge)) {
    return EDGE_STYLES.LOOP
  }
  if (isErrorEdge(edge)) {
    return EDGE_STYLES.ERROR
  }
  return EDGE_STYLES.NORMAL
}

/**
 * Apply all visual properties to an edge based on its type.
 * Single source of truth — used by createEdge, workflowToElements, and asyncConverter.
 *
 * @param {Object} edge - Raw edge object (must have at least source, target, data)
 * @returns {Object} Edge with all visual properties applied
 */
export function applyEdgeVisuals(edge) {
  const loop = isLoopEdge(edge)
  const error = isErrorEdge(edge)
  const edgeType = edge.data?.edgeType

  // Determine style + color
  let edgeStyle, pathType
  if (loop) {
    edgeStyle = EDGE_STYLES.LOOP
    pathType = 'smoothstep'
  } else if (error) {
    edgeStyle = EDGE_STYLES.ERROR
    pathType = 'smoothstep'
  } else if (edgeType === 'done') {
    edgeStyle = { stroke: '#10B981', strokeWidth: 2 }
    pathType = 'smoothstep'
  } else if (edgeType === 'resource') {
    edgeStyle = { stroke: '#9333ea', strokeWidth: 2 }
    pathType = 'bezier'
  } else {
    edgeStyle = EDGE_STYLES.NORMAL
    pathType = 'bezier'
  }

  return {
    ...edge,
    type: 'glow',
    style: { ...edgeStyle },
    markerEnd: { type: MarkerType.ArrowClosed, color: edgeStyle.stroke },
    animated: loop,
    ...(loop ? { class: 'loop-edge' } : {}),
    data: { ...edge.data, pathType }
  }
}
