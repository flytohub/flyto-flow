/**
 * Invite Keys API - Uses Gateway API
 * Handle invitation codes for early access
 */

import { get, post } from '@/api/client'
import { ENDPOINTS } from '@/api/config'
import { DEFAULTS } from '@/config/defaults'

export const inviteKeysAPI = {
  // ============== Admin endpoints ==============

  /**
   * List invite keys (admin only)
   * @param {Object} [params]
   * @param {string} [params.creatorId]
   * @param {string} [params.campaign]
   * @param {number} [params.page]
   * @param {number} [params.pageSize]
   * @returns {Promise<Object>}
   */
  async list({ creatorId = null, campaign = null, page = 1, pageSize = DEFAULTS.PAGINATION.DEFAULT } = {}) {
    try {
      const result = await get(ENDPOINTS.INVITE_KEYS.LIST, {
        params: { creatorId, campaign, page, pageSize }
      })
      return {
        ok: true,
        keys: result.keys || [],
        total: result.total || 0,
        page: result.page || page,
        pageSize: result.pageSize || pageSize
      }
    } catch (err) {
      return { ok: false, error: err.message, keys: [], total: 0 }
    }
  },

  /**
   * Get invite key by ID (admin only)
   * @param {string} keyId
   * @returns {Promise<Object>}
   */
  async get(keyId) {
    try {
      const result = await get(ENDPOINTS.INVITE_KEYS.GET(keyId))
      return { ok: true, key: result.key }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Get invite key statistics (admin only)
   * @param {string} [campaign]
   * @returns {Promise<Object>}
   */
  async getStats(campaign = null) {
    try {
      const result = await get(ENDPOINTS.INVITE_KEYS.STATS, {
        params: { campaign }
      })
      return { ok: true, stats: result.stats }
    } catch (err) {
      return { ok: false, error: err.message, stats: {} }
    }
  },

  /**
   * Create an invite key (admin only)
   * @param {Object} data
   * @param {number} [data.maxUses]
   * @param {string} [data.expiresAt]
   * @param {string} [data.note]
   * @param {string} [data.campaign]
   * @returns {Promise<Object>}
   */
  async create(data) {
    try {
      const result = await post(ENDPOINTS.INVITE_KEYS.CREATE, data)
      return { ok: true, key: result.key }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Batch create invite keys (admin only)
   * @param {Object} data
   * @param {number} data.count
   * @param {number} [data.maxUses]
   * @param {string} [data.expiresAt]
   * @param {string} [data.campaign]
   * @returns {Promise<Object>}
   */
  async batchCreate(data) {
    try {
      const result = await post(ENDPOINTS.INVITE_KEYS.BATCH_CREATE, data)
      return { ok: true, keys: result.keys, count: result.count }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Revoke an invite key (admin only)
   * @param {string} keyId
   * @returns {Promise<Object>}
   */
  async revoke(keyId) {
    try {
      await post(ENDPOINTS.INVITE_KEYS.REVOKE(keyId))
      return { ok: true }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }
}

export default inviteKeysAPI
