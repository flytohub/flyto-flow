/**
 * Subflow Tab Types
 *
 * S-Grade: Type definitions for subflow tab management.
 * Single responsibility: Type documentation.
 */

/**
 * Tab entry for subflow navigation
 * @typedef {Object} SubflowTab
 * @property {string} id - Unique tab ID
 * @property {string} flowId - The workflow/subflow ID
 * @property {string} label - Display label
 * @property {string|null} parentNodeId - Container node that owns this subflow
 * @property {number} depth - Nesting depth (0 = root)
 * @property {boolean} isDirty - Has unsaved changes
 * @property {Object|null} flowData - Optional flow data
 * @property {string|null} templateId - If set, this subflow references another local template
 */

/**
 * Breadcrumb entry for navigation
 * @typedef {Object} BreadcrumbItem
 * @property {string} id - Tab ID
 * @property {string} label - Display label
 * @property {number} depth - Nesting depth
 */

/**
 * Create a root tab entry
 * @param {string} flowId - Root flow ID
 * @param {string} flowName - Root flow display name
 * @returns {SubflowTab} Root tab entry
 */
export function createRootTab(flowId, flowName) {
  return {
    id: `tab_${flowId}`,
    flowId,
    label: flowName,
    parentNodeId: null,
    depth: 0,
    isDirty: false,
    flowData: null
  }
}

/**
 * Create a new subflow tab entry
 * @param {string} flowId - Subflow ID
 * @param {string} label - Display label
 * @param {string} parentNodeId - Parent container node ID
 * @param {number} depth - Nesting depth
 * @param {Object|null} flowData - Optional flow data
 * @returns {SubflowTab} New tab entry
 */
export function createSubflowTab(flowId, label, parentNodeId, depth, flowData = null, templateMeta = null) {
  return {
    id: `tab_${flowId}_${Date.now()}`,
    flowId,
    label: label || `Subflow ${depth}`,
    parentNodeId,
    depth,
    isDirty: false,
    flowData,
    templateId: templateMeta?.templateId || null
  }
}
