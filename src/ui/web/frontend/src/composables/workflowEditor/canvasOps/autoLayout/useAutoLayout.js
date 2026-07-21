/**
 * useAutoLayout - Backend-driven Auto Layout API
 *
 * All layout computation is done by the backend /workflows/layout API.
 * No local fallback — if backend fails, nodes stay in place.
 *
 * @example
 * const { layout } = useAutoLayout()
 * const newNodes = await layout(nodes, edges)
 */

import { workflowAPI } from '@/api/workflows'

/**
 * Layout Presets
 */
export const PRESETS = {
  default: { direction: 'RIGHT' },
  compact: { direction: 'RIGHT' },
  spacious: { direction: 'RIGHT' },
  vertical: { direction: 'DOWN' },
}

/**
 * Prepare nodes/edges payload for backend API
 */
function buildPayload(nodes, edges, options = {}) {
  return {
    nodes: nodes.map(n => ({
      id: n.id,
      module_id: n.data?.module || '',
      position_x: Math.round(n.position?.x ?? 0),
      position_y: Math.round(n.position?.y ?? 0),
      params: n.data?.params || {},
      data: n.data || {},
      ui_state: n.data?.ui_state || null,
    })),
    edges: edges.map(e => ({
      id: e.id,
      source: e.source,
      target: e.target,
      type: e.type,
      sourceHandle: e.sourceHandle,
      targetHandle: e.targetHandle,
      data: e.data || {},
    })),
    preset: options.preset || 'default',
    direction: options.direction || PRESETS[options.preset]?.direction || 'RIGHT',
  }
}

/**
 * Main layout function - backend-driven, no local fallback
 */
async function layout(nodes, edges = [], options = {}) {
  if (!nodes?.length) return nodes

  try {
    const payload = buildPayload(nodes, edges, options)
    const result = await workflowAPI.computeLayout(payload)

    if (!result?.ok || !result.positions) {
      return nodes
    }

    return nodes.map(node => {
      const pos = result.positions[node.id]
      return pos ? { ...node, position: { x: pos.x, y: pos.y } } : node
    })
  } catch (error) {
    return nodes
  }
}

/**
 * useAutoLayout composable
 */
export function useAutoLayout() {
  return {
    layout,
    presets: PRESETS,

    horizontal: (nodes, edges, opts = {}) =>
      layout(nodes, edges, { ...opts, direction: 'RIGHT' }),

    vertical: (nodes, edges, opts = {}) =>
      layout(nodes, edges, { ...opts, direction: 'DOWN' }),

    compact: (nodes, edges, opts = {}) =>
      layout(nodes, edges, { ...opts, preset: 'compact' }),

    spacious: (nodes, edges, opts = {}) =>
      layout(nodes, edges, { ...opts, preset: 'spacious' })
  }
}

export default useAutoLayout
