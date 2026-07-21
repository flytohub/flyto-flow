/**
 * Breadcrumb Utilities
 *
 * S-Grade: Breadcrumb building logic for subflow navigation.
 * Single responsibility: Build navigation breadcrumb trail.
 */

/**
 * Build breadcrumb trail from tabs
 * @param {Object} activeTab - Current active tab
 * @param {Array} allTabs - All tabs
 * @param {Object} rootTab - Root tab reference
 * @param {Function} getParentFlowId - Function to get parent flow ID
 * @returns {Array<BreadcrumbItem>} Breadcrumb items
 */
export function buildBreadcrumbs(activeTab, allTabs, rootTab, getParentFlowId) {
  if (!activeTab) {
    return [{ id: rootTab.id, label: rootTab.label, depth: 0 }]
  }

  // Build path from root to current
  let current = activeTab
  const path = [current]

  while (current.parentNodeId) {
    const parentTab = allTabs.find(t =>
      t.flowId === getParentFlowId(current.parentNodeId)
    )
    if (parentTab) {
      path.unshift(parentTab)
      current = parentTab
    } else {
      break
    }
  }

  // Ensure root is first
  if (path[0]?.depth !== 0) {
    path.unshift(rootTab)
  }

  return path.map(t => ({
    id: t.id,
    label: t.label,
    depth: t.depth
  }))
}

/**
 * Get parent flow ID from node and tabs
 * @param {string} nodeId - Node ID
 * @param {Array} allTabs - All tabs
 * @param {number} currentDepth - Current nesting depth
 * @param {string} rootFlowId - Root flow ID fallback
 * @returns {string} Parent flow ID
 */
export function findParentFlowId(nodeId, allTabs, currentDepth, rootFlowId) {
  for (const tab of allTabs) {
    if (tab.depth < currentDepth) {
      return tab.flowId
    }
  }
  return rootFlowId
}
