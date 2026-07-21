/**
 * AI agent resource slot rules.
 *
 * Backend workflow resources keep model and memory as single refs while tools
 * may contain multiple refs. These helpers keep the visual builder aligned with
 * that contract.
 */

const RESOURCE_HANDLE_TO_SLOT = {
  'target-model': 'model',
  'target-memory': 'memory',
  'target-tools': 'tools'
}

const RESOURCE_SLOT_LIMITS = {
  model: 1,
  memory: 1,
  tools: Infinity
}

function getEdgeTargetHandle(edge = {}) {
  return edge.targetHandle || edge.target_handle || ''
}

export function getResourceSlotType(targetHandle) {
  return RESOURCE_HANDLE_TO_SLOT[targetHandle] || null
}

export function getResourceSlotCounts(nodeId, edges = []) {
  const counts = { model: 0, memory: 0, tools: 0 }
  for (const edge of edges || []) {
    if (edge?.target !== nodeId) continue
    const slotType = getResourceSlotType(getEdgeTargetHandle(edge))
    if (!slotType) continue
    counts[slotType] += 1
  }
  return counts
}

export function getResourceSlotState(nodeId, edges = []) {
  const counts = getResourceSlotCounts(nodeId, edges)
  return Object.fromEntries(
    Object.entries(counts).map(([slotType, count]) => {
      const limit = RESOURCE_SLOT_LIMITS[slotType]
      return [
        slotType,
        {
          count,
          limit,
          locked: Number.isFinite(limit) && count >= limit
        }
      ]
    })
  )
}

export function canAddResourceToHandle(nodeId, targetHandle, edges = []) {
  const slotType = getResourceSlotType(targetHandle)
  if (!slotType) return true
  const limit = RESOURCE_SLOT_LIMITS[slotType]
  if (!Number.isFinite(limit)) return true
  return getResourceSlotCounts(nodeId, edges)[slotType] < limit
}
