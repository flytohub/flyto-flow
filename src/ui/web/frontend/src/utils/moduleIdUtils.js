/**
 * Module ID Utilities - Simplified
 *
 * Design: Backend is single source of truth.
 * - isTemplate flag comes from backend metadata
 * - Pattern matching is fallback only for edge cases
 */

/**
 * Get base module type for node type checks
 *
 * Used to check node behavior (isLoopNode, isBranchNode, etc.)
 * Template modules: "template.invoke:xxx" -> "template.invoke"
 * Regular modules: "browser.click" -> "browser.click"
 *
 * @param {string} moduleId - Module ID
 * @returns {string} Base module type
 */
export function getBaseModuleType(moduleId) {
  if (!moduleId) return ''
  if (moduleId.startsWith('template.invoke:')) {
    return 'template.invoke'
  }
  return moduleId
}

/**
 * Check if module ID represents a template module
 *
 * Backend is single source of truth via isTemplate flag.
 * Pattern matching is fallback for edge cases (e.g., before metadata loads).
 *
 * @param {string} moduleId - Module ID
 * @param {object} modulesStore - Optional Pinia modules store for backend flag lookup
 * @returns {boolean} True if template module
 */
/**
 * Resolve a human-readable label for a module ID.
 *
 * Looks up modulesStore metadata first (label from core),
 * falls back to title-casing the last segment of the module ID.
 *
 * @param {string} moduleId - Module ID (e.g. "browser.goto")
 * @param {object} modulesStore - Pinia modules store
 * @returns {string} Resolved label
 */
export function resolveModuleLabel(moduleId, modulesStore = null) {
  if (!moduleId) return ''

  // Priority 1: backend metadata label (from core)
  const metadata = modulesStore?.modulesMetadata?.[moduleId]
  if (metadata?.label) return metadata.label

  // Priority 2: title-case the last segment
  const parts = moduleId.split('.')
  return parts[parts.length - 1]
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

export function isTemplateModule(moduleId, modulesStore = null) {
  if (!moduleId) return false

  // Use backend isTemplate flag if available
  const metadata = modulesStore?.modulesMetadata?.[moduleId]
  if (metadata?.isTemplate !== undefined) {
    return metadata.isTemplate
  }

  // Fallback: pattern matching (only for edge cases)
  return moduleId.startsWith('template.invoke')
}
