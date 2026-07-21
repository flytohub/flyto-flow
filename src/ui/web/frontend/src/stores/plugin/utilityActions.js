/**
 * Plugin Utility Actions
 *
 * S-Grade: Utility actions.
 * Single responsibility: Status, cache, and reset operations.
 */

import { pluginAPI } from '@/api/plugins'
import i18n from '@/i18n'

/**
 * Create utility actions
 * @param {Object} state - State refs
 * @returns {Object} Utility action functions
 */
export function createUtilityActions(state) {
  const {
    searchResults,
    installedPlugins,
    selectedPlugin,
    cacheStats,
    isLoading,
    isInstalling,
    error
  } = state

  /**
   * Get model status
   */
  async function getStatus(modelId) {
    try {
      const result = await pluginAPI.getStatus(modelId)
      return result
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  /**
   * Fetch cache stats
   */
  async function fetchCacheStats() {
    isLoading.value = true
    error.value = null

    try {
      const result = await pluginAPI.getCacheStats()
      if (result.ok) {
        cacheStats.value = result.data
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchCacheStats')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Set selected plugin
   */
  function setSelectedPlugin(plugin) {
    selectedPlugin.value = plugin
  }

  /**
   * Clear error
   */
  function clearError() {
    error.value = null
  }

  /**
   * Reset state
   */
  function reset() {
    searchResults.value = []
    installedPlugins.value = []
    selectedPlugin.value = null
    cacheStats.value = null
    isLoading.value = false
    isInstalling.value = false
    error.value = null
  }

  return {
    getStatus,
    fetchCacheStats,
    setSelectedPlugin,
    clearError,
    reset,
  }
}
