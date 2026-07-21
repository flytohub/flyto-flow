/**
 * Platform Config API
 * Centralized configuration from backend
 *
 * S-Grade: All frontend configuration comes from backend.
 * No hardcoded values in frontend code.
 */

import { get } from './client'

// =============================================================================
// Cache Management
// =============================================================================

let _configCache = null
let _cacheTimestamp = null
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

function isCacheValid() {
  return _configCache && _cacheTimestamp && (Date.now() - _cacheTimestamp < CACHE_TTL)
}

// =============================================================================
// Main Config API
// =============================================================================

/**
 * Get all frontend configuration in a single request
 * This is the primary method - use this at app startup
 * @param {Object} options
 * @param {boolean} options.forceRefresh - Force refresh from server
 * @returns {Promise<Object>} All configuration
 */
export async function getAllConfig({ forceRefresh = false } = {}) {
  if (!forceRefresh && isCacheValid()) {
    return _configCache
  }

  const response = await get('/config/all')
  if (response.ok) {
    _configCache = response.config
    _cacheTimestamp = Date.now()
    return _configCache
  }

  throw new Error(response.error || 'Failed to fetch config')
}

// =============================================================================
// Export
// =============================================================================

export const platformAPI = {
  getAllConfig
}

export default platformAPI
