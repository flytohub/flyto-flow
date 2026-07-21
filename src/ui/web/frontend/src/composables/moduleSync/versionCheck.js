/**
 * Version Check Utilities
 *
 * S-Grade: Module version checking.
 * Single responsibility: Fetch and compare module versions.
 */

import { API_URL } from '@/config/api'
import { clearModuleCache, getCachedVersion, setCachedVersion } from './cacheUtils'

/**
 * Fetch current module version from backend
 * @returns {Promise<Object|null>}
 */
export async function fetchModuleVersion() {
  try {
    const response = await fetch(`${API_URL}/modules/version`)
    if (response.ok) {
      const data = await response.json()
      return data
    }
  } catch (e) {
    // Silent fail
  }
  return null
}

/**
 * Check if modules have been updated
 * @param {Function} onUpdate - Callback with version info and refs to update
 * @returns {Promise<boolean>} True if updated
 */
export async function checkForModuleUpdates(onUpdate) {
  const versionInfo = await fetchModuleVersion()
  if (!versionInfo) return false

  const cachedVersion = getCachedVersion()
  const newVersion = versionInfo.version

  if (cachedVersion !== newVersion) {
    // Clear cache and update version
    clearModuleCache()
    setCachedVersion(newVersion)

    // Notify caller
    if (onUpdate) {
      onUpdate(versionInfo)
    }

    // Emit custom event for other components to react
    window.dispatchEvent(new CustomEvent('modules-updated', {
      detail: versionInfo
    }))

    return true
  }

  return false
}

/**
 * Manually trigger module reload
 * @param {Object} options
 * @param {boolean} options.gitPull - Pull from git
 * @param {boolean} options.force - Force reload
 * @returns {Promise<Object>}
 */
export async function triggerModuleReload(options = {}) {
  const { gitPull = false, force = false } = options

  const endpoint = gitPull
    ? `${API_URL}/modules/reload?force=${force}`
    : `${API_URL}/modules/reload/local?force=${force}`

  const response = await fetch(endpoint, { method: 'POST' })
  const data = await response.json()

  if (response.ok) {
    return data
  } else {
    throw new Error(data.detail || 'Reload failed')
  }
}
