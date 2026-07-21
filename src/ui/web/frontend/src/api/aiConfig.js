/**
 * AI Configuration API - BYOK (Bring Your Own Key)
 *
 * Manages AI provider settings (API keys, model selection, etc.)
 */

import { get, post } from '@/api/client'
import { ENDPOINTS } from '@/api/config'

export const aiConfigAPI = {
  /**
   * Get current AI configuration (API key is masked)
   * @returns {Promise<Object>} { ok, configured, config: { provider, api_key_masked, model, ... } }
   */
  async getConfig() {
    try {
      return await get(ENDPOINTS.AI.CONFIG)
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Save AI configuration
   * @param {Object} config - Configuration to save
   * @param {string} config.provider - 'openai' | 'anthropic'
   * @param {string} [config.apiKey] - API key (omit to keep existing)
   * @param {string} [config.model] - Model name
   * @param {number} [config.temperature] - Temperature (0-2)
   * @param {number} [config.maxTokens] - Max tokens
   * @param {string} [config.baseUrl] - Custom base URL
   * @returns {Promise<Object>} { ok, message }
   */
  async saveConfig({ provider, apiKey, model, temperature, maxTokens, baseUrl, autoImport, autoExecute }) {
    try {
      return await post(ENDPOINTS.AI.CONFIG, {
        provider,
        apiKey,
        model: model || '',
        temperature: temperature ?? 0.7,
        maxTokens: maxTokens ?? 4096,
        baseUrl: baseUrl || '',
        autoImport: autoImport ?? undefined,
        autoExecute: autoExecute ?? undefined
      })
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Test API key / connection
   * @param {Object} params - Test parameters
   * @param {string} params.provider - Provider to test
   * @param {string} [params.apiKey] - API key to test
   * @param {string} [params.model] - Model to test with
   * @param {string} [params.baseUrl] - Custom base URL
   * @returns {Promise<Object>} { ok, message, models? }
   */
  async testConnection({ provider, apiKey, model, baseUrl }) {
    try {
      return await post(ENDPOINTS.AI.CONFIG_TEST, {
        provider,
        apiKey,
        model,
        baseUrl
      })
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }
}

export default aiConfigAPI
