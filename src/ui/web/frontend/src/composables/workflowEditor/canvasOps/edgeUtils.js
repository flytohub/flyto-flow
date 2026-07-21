/**
 * Edge Utilities
 *
 * S-Grade: Single responsibility - edge creation and utilities only.
 */

import {
  EDGE_PREFIXES,
  EDGE_STYLES,
  getRandomSuffix,
  applyEdgeVisuals,
} from '../workflowConstants'
import { MarkerType } from '@vue-flow/core'

// Counter for ensuring unique IDs within the same millisecond
let edgeIdCounter = 0

// VueFlow default edge options (used by WorkflowCanvas <VueFlow :default-edge-options>)
export const DEFAULT_EDGE_OPTIONS = { type: 'glow' }
export const EDGE_STYLE = EDGE_STYLES.NORMAL
export const EDGE_MARKER = { type: MarkerType.ArrowClosed, color: EDGE_STYLES.NORMAL.stroke }

/**
 * Get automatic label for branch/switch/loop edges based on source handle
 * @param {string|null} sourceHandle - Source handle ID
 * @param {Object|null} sourceNodeData - Source node .data (for case label lookup)
 * @returns {string|null} Label or null if no auto-label
 */
function getAutoLabelForHandle(sourceHandle, sourceNodeData = null) {
  if (!sourceHandle) return null

  // Branch node handles
  if (sourceHandle === 'source-true') return 'True'
  if (sourceHandle === 'source-false') return 'False'

  // Loop node handles
  if (sourceHandle === 'body_out') return 'Iterate'
  if (sourceHandle === 'done_out') return 'Done'

  // Error handle
  if (sourceHandle === 'source-error') return 'Error'

  // Switch node default
  if (sourceHandle === 'source-default') return 'Default'

  // Switch node case handles (source-case-xxx) — look up label from params
  if (sourceHandle.startsWith('source-case-')) {
    const caseId = sourceHandle.replace('source-case-', '')
    const cases = sourceNodeData?.params?.cases || []
    const matched = cases.find(c => c.id === caseId)
    return matched?.label || matched?.value || caseId
  }

  return null
}

/**
 * Create a new edge object
 * Uses timestamp + counter + random suffix to prevent collisions.
 * Visual properties are applied by applyEdgeVisuals (single source of truth).
 *
 * @param {string} sourceId - Source node ID
 * @param {string} targetId - Target node ID
 * @param {string|null} sourceHandle - Source handle ID
 * @param {string|null} targetHandle - Target handle ID
 * @param {Object} options - Additional options
 * @param {string} options.color - Custom edge color (for switch cases, branches)
 * @param {string} options.label - Custom label (overrides auto-label)
 * @param {Object} options.sourceNodeData - Source node .data (for case label lookup)
 */
export function createEdge(sourceId, targetId, sourceHandle = null, targetHandle = null, options = {}) {
  const isLoop = sourceHandle === 'body_out'
  const isError = sourceHandle === 'source-error'

  // Error edges flow downward (bottom→top), so auto-target the top handle
  if (isError && !targetHandle) {
    targetHandle = 'target-top'
  }
  const uniqueSuffix = `${Date.now()}_${edgeIdCounter++}_${getRandomSuffix()}`

  // Auto-generate label based on source handle (can be overridden by options.label)
  const autoLabel = getAutoLabelForHandle(sourceHandle, options.sourceNodeData)
  const edgeLabel = options.label !== undefined ? options.label : autoLabel

  // Build raw edge with structural data
  const edgePrefix = isLoop ? EDGE_PREFIXES.LOOP : isError ? EDGE_PREFIXES.ERROR : EDGE_PREFIXES.NORMAL
  const rawEdge = {
    id: `${edgePrefix}${sourceId}_${targetId}${targetHandle ? `_${targetHandle}` : ''}_${uniqueSuffix}`,
    source: sourceId,
    target: targetId,
    data: {
      edgeType: options.edgeType || (isLoop ? 'iterate' : 'main'),
      ...(edgeLabel ? { label: edgeLabel } : {}),
      ...(options.color ? { edgeColor: options.color } : {}),
      ...(options.data || {})
    }
  }

  if (sourceHandle) rawEdge.sourceHandle = sourceHandle
  if (targetHandle) rawEdge.targetHandle = targetHandle

  // Apply unified visual properties
  const edge = applyEdgeVisuals(rawEdge)

  // Override style with custom color if provided (for branch/switch edges)
  if (options.color) {
    edge.style = { ...edge.style, stroke: options.color }
    edge.markerEnd = { ...edge.markerEnd, color: options.color }
  }

  return edge
}

/**
 * Filter edges from elements array
 */
export function filterEdges(elements) {
  if (!elements || !Array.isArray(elements)) return []
  return elements.filter(el => el && el.source)
}
