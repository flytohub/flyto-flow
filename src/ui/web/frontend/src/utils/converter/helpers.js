/**
 * Converter Helper Utilities
 *
 * S-Grade: Miscellaneous helper functions for step conversion.
 * Single source of truth for converter utilities.
 *
 * SECURITY NOTE:
 * Permission extraction (extractRequiredPermissions) is for UI display only.
 * Actual permission validation must happen server-side.
 * Backend module metadata should include `requiredPermissions` field.
 */

import { HANDLE_IDS } from '@/composables/workflowEditor/workflowConstants'


/**
 * Extract raw module ID string from node data or value
 * Handles various node data structures including nested objects.
 * This is the SINGLE source of truth for module ID extraction.
 *
 * @param {*} value - Node data object or module value
 * @returns {string} Extracted module ID or empty string
 */
export function extractRawModuleId(value) {
  if (!value) return ''
  if (typeof value === 'string') return value

  if (typeof value === 'object') {
    // Handle node.data structure
    const data = value.data || value
    const candidates = [
      data.module,
      data.moduleId,
      data?.module?.moduleId,
      data?.module?.id,
      data?.module?.module
    ]

    for (const item of candidates) {
      if (!item) continue
      if (typeof item === 'string') return item
      if (typeof item === 'object') {
        const resolved = item.moduleId || item.id || item.module
        if (resolved) return resolved
      }
    }
  }

  return ''
}

/**
 * Permission map for module categories (UI HINTS ONLY)
 *
 * SECURITY NOTE: This is for UI display purposes only.
 * Actual permission validation must happen server-side.
 * Backend should provide requiredPermissions in module metadata.
 *
 * @deprecated Prefer using module.metadata.requiredPermissions from backend
 */
const PERMISSION_MAP = {
  browser: ['browser_automation'],
  api: ['network_access'],
  file: ['file_system'],
  notify: ['notifications'],
  discord: ['network_access', 'webhooks'],
  telegram: ['network_access', 'webhooks'],
  email: ['network_access', 'email_send'],
  database: ['database_access'],
  schedule: ['background_tasks']
}

/**
 * Extract required permissions from steps (UI HINTS ONLY)
 *
 * SECURITY NOTE: This function provides UI hints only.
 * Actual permission enforcement must happen server-side.
 *
 * Prefer using module metadata from backend when available:
 * - module.metadata.requiredPermissions
 * - /api/modules/{id} response includes permissions
 *
 * @param {Array} steps - Backend steps
 * @param {Object} options - Options
 * @param {Object} options.modulesStore - Modules store for metadata lookup
 * @returns {Array} Required permission strings
 * @deprecated Use backend module metadata for authoritative permissions
 */
export function extractRequiredPermissions(steps, options = {}) {
  const { modulesStore } = options
  const requiredPermissions = new Set()

  steps.forEach(step => {
    const module = step.module || ''

    // First, try to get permissions from backend module metadata (authoritative)
    if (modulesStore) {
      const moduleData = modulesStore.getModule?.(module)
      if (moduleData?.metadata?.requiredPermissions) {
        moduleData.metadata.requiredPermissions.forEach(perm =>
          requiredPermissions.add(perm)
        )
        return
      }
    }

    // Fallback to local mapping (UI hint only)
    const category = module.split('.')[0]
    if (PERMISSION_MAP[category]) {
      PERMISSION_MAP[category].forEach(perm => requiredPermissions.add(perm))
    }
  })

  return Array.from(requiredPermissions)
}

/**
 * Debug helper - log step format
 * @deprecated This is a no-op function kept for backward compatibility
 * @param {string} label - Debug label
 * @param {Array} steps - Steps to log
 */
export function debugLogSteps(label, steps) {
  // No-op: debug logging disabled
}

/**
 * Resolve switch case key from edge to backend format
 * Converts VueFlow edge sourceHandle to backend case key format (case:xxx)
 *
 * @param {Object} edge - VueFlow edge object
 * @param {Object} nodeParams - Node params containing cases array
 * @returns {string|null} Case key in format "case:xxx" or null
 */
export function resolveSwitchCaseKey(edge, nodeParams) {
  if (!edge) return null
  const handle = edge.sourceHandle || ''
  const edgeCaseId = edge.data?.caseId || edge.data?.caseKey

  // Handle format: source-case-{caseId}
  if (handle.startsWith('source-case-')) {
    const caseId = handle.replace('source-case-', '')
    return `case:${caseId}`
  }

  // Handle format: source-cases (legacy/fallback)
  if (handle === 'source-cases') {
    if (edgeCaseId) return `case:${edgeCaseId}`
    const cases = nodeParams?.cases || []
    if (cases.length === 1 && cases[0]?.id) return `case:${cases[0].id}`
  }

  return null
}

/**
 * Resolve switch case handle ID from backend format to VueFlow handle
 * Converts backend case key (case:xxx) to VueFlow sourceHandle format
 *
 * @param {string} caseKey - Backend case key in format "case:xxx"
 * @param {Array} cases - Array of case definitions from node params
 * @returns {string|null} VueFlow handle ID or null
 */
export function resolveSwitchCaseHandleId(caseKey, cases = []) {
  if (!caseKey || !caseKey.startsWith('case:')) return null

  const caseValue = caseKey.replace('case:', '')
  const match = Array.isArray(cases)
    ? cases.find(item => String(item?.id) === caseValue || String(item?.value) === caseValue)
    : null
  const caseId = match?.id ?? caseValue

  return `${HANDLE_IDS.CASE_PREFIX}${caseId}`
}

/**
 * Parse params ensuring it's always an object
 * Handles string JSON, arrays, and nested structures
 *
 * @param {*} params - Raw params value
 * @param {string} context - Context for logging (optional)
 * @param {number} depth - Current parse depth (internal)
 * @returns {Object} Parsed params object
 */
const MAX_PARSE_DEPTH = 3

export function parseParams(params, context = '', depth = 0) {
  // Guard against infinite recursion from nested JSON strings
  if (depth >= MAX_PARSE_DEPTH) {
    return typeof params === 'object' && params !== null ? params : {}
  }

  if (typeof params === 'string') {
    if (params.trim() === '') return {}
    try {
      const parsed = JSON.parse(params)
      if (typeof parsed === 'string') {
        return parseParams(parsed, context, depth + 1)
      }
      if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
        return parsed
      }
      return {}
    } catch {
      return {}
    }
  }

  // Handle array params by attempting recovery (merge objects)
  if (Array.isArray(params)) {
    const paramsObj = {}
    params.forEach(item => {
      if (item && typeof item === 'object') Object.assign(paramsObj, item)
    })
    return paramsObj
  }

  return params || {}
}
