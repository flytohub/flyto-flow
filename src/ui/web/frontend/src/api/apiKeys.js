/**
 * API Keys API - User API Key Management
 * Provides API layer for MyApiKeys.vue
 */

import { get, post, del } from '@/api/client'
import { ENDPOINTS } from '@/config/api'

/**
 * List user's API keys
 * @returns {Promise<{ok: boolean, apiKeys: Array}>}
 */
export async function list() {
  try {
    const result = await get(ENDPOINTS.API_KEYS.LIST)
    return {
      ok: true,
      apiKeys: result.apiKeys || result.data || []
    }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message, apiKeys: [] }
  }
}

/**
 * Get API key by ID
 * @param {string} id - API key ID
 * @returns {Promise<{ok: boolean, apiKey: Object}>}
 */
export async function getById(id) {
  try {
    const result = await get(ENDPOINTS.API_KEYS.GET(id))
    return { ok: true, apiKey: result.apiKey || result }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Create a new API key
 * @param {Object} data - API key data
 * @param {string} data.name - Key name
 * @param {string} [data.expiresAt] - Expiration date (ISO string)
 * @param {string[]} [data.scopes] - Key scopes
 * @returns {Promise<{ok: boolean, apiKey: string, keyInfo: Object}>}
 */
export async function create(data) {
  try {
    const result = await post(ENDPOINTS.API_KEYS.CREATE, data)
    return {
      ok: true,
      apiKey: result.apiKey || result.key,
      keyInfo: result.keyInfo || result
    }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Revoke an API key (makes it inactive but keeps the record)
 * @param {string} id - API key ID
 * @returns {Promise<{ok: boolean}>}
 */
export async function revoke(id) {
  try {
    await post(ENDPOINTS.API_KEYS.REVOKE(id))
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Delete an API key (permanently removes)
 * @param {string} id - API key ID
 * @returns {Promise<{ok: boolean}>}
 */
export async function remove(id) {
  try {
    await del(ENDPOINTS.API_KEYS.DELETE(id))
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

export const apiKeysAPI = {
  list,
  get: getById,
  create,
  revoke,
  delete: remove
}

export default apiKeysAPI
