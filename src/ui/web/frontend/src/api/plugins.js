/**
 * Plugin API Client
 *
 * Simplified plugin management:
 * - Search/Browse: HuggingFace API
 * - Install/Uninstall: Local folder management
 */

import { get, post, del } from './client'
import i18n from '@/i18n'

const PLUGIN_BASE = '/plugins'

/**
 * Wrap API response in standard format
 */
function wrapResponse(data) {
  return { ok: true, data: data?.data || data }
}

/**
 * Handle API errors
 */
function handleError(error) {
  const errorMsg = error.response?.data?.detail || error.response?.data?.error || error.message || i18n.global.t('error.networkError')
  if (import.meta.env.DEV) {
  }
  return {
    ok: false,
    error: errorMsg
  }
}

export const pluginAPI = {
  /**
   * Search for models on HuggingFace Hub
   * @param {Object} params - Search parameters
   * @param {string} params.query - Search query
   * @param {string} [params.task] - Filter by task type
   * @param {number} [params.limit] - Maximum results
   * @param {number} [params.offset] - Offset for pagination
   * @returns {Promise<Object>} Search results
   */
  async searchModels({ query, task, limit = 20, offset = 0 }) {
    try {
      const params = new URLSearchParams({ query, limit: limit.toString(), offset: offset.toString() })
      if (task) params.append('task', task)
      const data = await get(`${PLUGIN_BASE}/search?${params.toString()}`)
      return wrapResponse(data)
    } catch (error) {
      return handleError(error)
    }
  },

  /**
   * Get model information from HuggingFace
   * @param {string} modelId - Model ID
   * @returns {Promise<Object>} Model info
   */
  async getModelInfo(modelId) {
    try {
      const data = await get(`${PLUGIN_BASE}/info/${encodeURIComponent(modelId)}`)
      return wrapResponse(data)
    } catch (error) {
      return handleError(error)
    }
  },

  /**
   * List installed plugins
   * @param {Object} [params] - Filter parameters
   * @param {string} [params.category] - Filter by category
   * @param {string} [params.task] - Filter by task
   * @returns {Promise<Object>} Installed plugins list
   */
  async listInstalled({ category, task } = {}) {
    try {
      const params = new URLSearchParams()
      if (category) params.append('category', category)
      if (task) params.append('task', task)
      const queryString = params.toString()
      const data = await get(`${PLUGIN_BASE}/installed${queryString ? `?${queryString}` : ''}`)
      return wrapResponse(data)
    } catch (error) {
      return handleError(error)
    }
  },

  /**
   * Install a model from HuggingFace Hub
   * @param {string} modelId - Model ID to install
   * @returns {Promise<Object>} Installation result
   */
  async installModel(modelId) {
    try {
      const data = await post(`${PLUGIN_BASE}/install/${encodeURIComponent(modelId)}`)
      return wrapResponse(data)
    } catch (error) {
      return handleError(error)
    }
  },

  /**
   * Uninstall a model
   * @param {string} modelId - Model ID to uninstall
   * @returns {Promise<Object>} Uninstall result
   */
  async uninstallModel(modelId) {
    try {
      const data = await del(`${PLUGIN_BASE}/uninstall/${encodeURIComponent(modelId)}`)
      return wrapResponse(data)
    } catch (error) {
      return handleError(error)
    }
  },

  /**
   * Get model status
   * @param {string} modelId - Model ID
   * @returns {Promise<Object>} Model status
   */
  async getStatus(modelId) {
    try {
      const data = await get(`${PLUGIN_BASE}/status/${encodeURIComponent(modelId)}`)
      return wrapResponse(data)
    } catch (error) {
      return handleError(error)
    }
  },

  /**
   * Get cache statistics
   * @returns {Promise<Object>} Cache stats
   */
  async getCacheStats() {
    try {
      const data = await get(`${PLUGIN_BASE}/cache/stats`)
      return wrapResponse(data)
    } catch (error) {
      return handleError(error)
    }
  }
}

export default pluginAPI
