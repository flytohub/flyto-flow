/**
 * Module Cache Utilities
 *
 * S-Grade: Module cache operations.
 * Single responsibility: Clear and manage module caches.
 */

import { DEFAULTS } from '@/config/defaults'

const MODULE_VERSION_KEY = DEFAULTS.STORAGE_KEYS.MODULE_VERSION
const MODULE_CACHE_PREFIX = DEFAULTS.STORAGE_KEYS.MODULE_CACHE_PREFIX

/**
 * Clear all module caches from localStorage
 */
export function clearModuleCache() {
  const keysToRemove = []
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(MODULE_CACHE_PREFIX)) {
      keysToRemove.push(key)
    }
  }
  keysToRemove.forEach(key => localStorage.removeItem(key))
}

/**
 * Get cached module version
 * @returns {string|null}
 */
export function getCachedVersion() {
  return localStorage.getItem(MODULE_VERSION_KEY)
}

/**
 * Set cached module version
 * @param {string} version
 */
export function setCachedVersion(version) {
  localStorage.setItem(MODULE_VERSION_KEY, version)
}

export { MODULE_VERSION_KEY, MODULE_CACHE_PREFIX }
