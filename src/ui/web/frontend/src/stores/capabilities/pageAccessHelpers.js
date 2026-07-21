/**
 * Page Access Helpers
 *
 * S-Grade: Page access logic extracted from capabilities store.
 * Single responsibility: route access control.
 *
 * SECURITY NOTE:
 * The ALWAYS_ALLOWED_PAGES list is for CLIENT-SIDE routing only.
 * Actual page access is enforced by:
 * 1. Backend /api/capabilities returns 'pages' object with allowed routes
 * 2. Backend API endpoints validate access on each request
 * 3. Route guards use backend-provided config, not this static list
 *
 * This list provides a fallback for offline scenarios and initial load.
 * Backend pages config is authoritative - see capabilities.pages response.
 *
 * Never use this list alone for access control decisions.
 */

/**
 * Pages always accessible to logged-in users (FALLBACK ONLY)
 *
 * SECURITY NOTE: This is a client-side fallback list.
 * Backend /api/capabilities returns authoritative 'pages' config.
 * Prefer using capabilities.pages from backend response.
 *
 * This list should be kept minimal and include only:
 * - Authentication routes (login, logout)
 * - Core functionality available to all users
 * - Routes that don't require feature checks
 *
 * @deprecated Prefer using backend-provided pages config
 */
export const ALWAYS_ALLOWED_PAGES = [
  '/',
  '/login',
  '/dashboard',
  '/my-templates',
  '/templates',
  '/templates/builder',
  '/workflows',
  '/settings'
]

/**
 * Check if path is in always-allowed list
 *
 * SECURITY NOTE: This is for client-side routing fallback.
 * Backend validates actual access on API requests.
 *
 * @param {string} path - Route path
 * @returns {boolean}
 */
export function isAlwaysAllowed(path) {
  return ALWAYS_ALLOWED_PAGES.some(p => path === p || path.startsWith(p + '/'))
}

/**
 * Check page access against pages config from backend
 *
 * This function uses the AUTHORITATIVE pages config from backend.
 * The pagesConfig parameter should come from /api/capabilities response.
 *
 * @param {string} path - Route path
 * @param {Object} pagesConfig - Pages configuration from backend API
 * @returns {boolean|null} - true/false if match found, null if no match
 */
export function checkPageAccess(path, pagesConfig) {
  // Exact match from backend config
  if (pagesConfig[path] !== undefined) {
    return pagesConfig[path]
  }

  // Wildcard match from backend config
  for (const [pattern, allowed] of Object.entries(pagesConfig)) {
    if (pattern.endsWith('/*')) {
      const prefix = pattern.slice(0, -1)
      if (path.startsWith(prefix)) {
        return allowed
      }
    }
  }

  return null
}

/**
 * Build canAccessPage function with backend config
 *
 * SECURITY NOTE: The pagesConfig MUST come from backend /api/capabilities.
 * This creates a checker that:
 * 1. First checks the authoritative backend config
 * 2. Falls back to ALWAYS_ALLOWED_PAGES only if no config match
 *
 * @param {Object} pagesConfig - Pages configuration from backend
 * @returns {Function} Access check function
 */
export function createPageAccessChecker(pagesConfig) {
  return (path) => {
    // First check backend config (authoritative)
    const configResult = checkPageAccess(path, pagesConfig)
    if (configResult !== null) return configResult

    // Fallback to always-allowed list only if backend has no config
    if (isAlwaysAllowed(path)) return true

    // Default deny if not in any allowed list
    return false
  }
}
