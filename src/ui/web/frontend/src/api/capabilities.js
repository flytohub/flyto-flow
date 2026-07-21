/**
 * Capabilities API
 * Fetch system capabilities for current deployment mode
 */

import { get, post } from './client'

/**
 * Get system capabilities
 * Returns deployment mode, available capabilities, feature flags,
 * page visibility, and UI configuration hints.
 *
 * @returns {Promise<Object>} Capabilities response
 * @example
 * {
 *   deployment_mode: 'cloud' | 'enterprise',
 *   license_type: 'free' | 'subscription' | 'offline_license' | 'enterprise',
 *   is_licensed: true,
 *   capabilities: ['auth.firebase', 'marketplace', ...],
 *   features: { marketplace: true, billing: true, rbac: false, ... },
 *   pages: { '/marketplace': true, '/admin/rbac': false, ... },
 *   ui: { showMarketplace: true, authMethod: 'firebase', ... }
 * }
 */
export async function getCapabilities() {
  try {
    return await get('/capabilities')
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Reload capabilities from license file
 * Call after license activation to refresh context
 *
 * @returns {Promise<Object>} Updated capabilities
 */
export async function reloadCapabilities() {
  try {
    return await post('/capabilities/reload')
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

export const capabilitiesAPI = {
  getCapabilities,
  reloadCapabilities
}

export default capabilitiesAPI
