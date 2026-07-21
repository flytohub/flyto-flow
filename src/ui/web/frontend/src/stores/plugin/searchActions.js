/**
 * Plugin Search Actions
 *
 * S-Grade: Search and model info actions.
 * Single responsibility: Search plugin operations.
 */

import { pluginAPI } from '@/api/plugins'
import i18n from '@/i18n'
import { telemetry } from '@/services/telemetry'

/**
 * Create search actions
 * @param {Object} state - State refs
 * @returns {Object} Search action functions
 */
export function createSearchActions(state) {
  const { searchResults, selectedPlugin, isLoading, error } = state

  /**
   * Search for models
   * @param {Object} params - Search parameters
   * @param {boolean} params.append - If true, append to existing results instead of replacing
   * @param {number} params.offset - Offset for pagination
   */
  async function searchModels(params) {
    isLoading.value = true
    error.value = null
    const { append, offset = 0, ...searchParams } = params
    searchParams.offset = offset

    try {
      const result = await pluginAPI.searchModels(searchParams)
      if (result.ok) {
        const newModels = result.data?.models || result.data || []
        if (append) {
          // Append and deduplicate by model_id
          const existingIds = new Set(searchResults.value.map(m => m.model_id))
          const uniqueNew = newModels.filter(m => !existingIds.has(m.model_id))
          searchResults.value = [...searchResults.value, ...uniqueNew]
        } else {
          searchResults.value = newModels
        }
        telemetry.track('plugin.search', {
          query: searchParams.search || searchParams.query,
          results_count: searchResults.value.length
        })
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToSearchModels')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get model info
   */
  async function getModelInfo(modelId) {
    isLoading.value = true
    error.value = null

    try {
      const result = await pluginAPI.getModelInfo(modelId)
      if (result.ok) {
        selectedPlugin.value = result.data
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToGetModelInfo')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Clear search results
   */
  function clearSearch() {
    searchResults.value = []
  }

  return {
    searchModels,
    getModelInfo,
    clearSearch,
  }
}
