/**
 * Reports API - Uses Gateway API
 * Handle content reports (moderation)
 */

import { get, post, put, del } from '@/api/client'
import { ENDPOINTS } from '@/api/config'
import { DEFAULTS } from '@/config/defaults'

// Report target types
export const ReportTargetType = {
  TEMPLATE: 'template',
  USER: 'user',
  REVIEW: 'review',
  MESSAGE: 'message'
}

// Report status
export const ReportStatus = {
  PENDING: 'pending',
  REVIEWING: 'reviewing',
  RESOLVED: 'resolved',
  DISMISSED: 'dismissed'
}

export const reportsAPI = {
  /**
   * Create a content report (requires auth)
   * @param {Object} data
   * @param {string} data.target_type - template, user, review, message
   * @param {string} data.target_id
   * @param {string} data.reason
   * @param {string} [data.details]
   * @returns {Promise<Object>}
   */
  async create(data) {
    try {
      const result = await post(ENDPOINTS.REPORTS.CREATE, data)
      return { ok: true, report: result.report }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * List my submitted reports (requires auth)
   * @param {Object} [params]
   * @param {number} [params.page]
   * @param {number} [params.page_size]
   * @returns {Promise<Object>}
   */
  async listMyReports({ page = 1, page_size = DEFAULTS.PAGINATION.DEFAULT } = {}) {
    try {
      const result = await get(ENDPOINTS.REPORTS.MY_REPORTS, {
        params: { page, page_size }
      })
      return {
        ok: true,
        reports: result.reports || [],
        total: result.total || 0,
        page: result.page || page,
        pageSize: result.pageSize || pageSize
      }
    } catch (err) {
      return { ok: false, error: err.message, reports: [], total: 0 }
    }
  },

  // ============== Admin endpoints ==============

  /**
   * List all reports (admin only)
   * @param {Object} [params]
   * @param {string} [params.status]
   * @param {string} [params.target_type]
   * @param {number} [params.page]
   * @param {number} [params.page_size]
   * @returns {Promise<Object>}
   */
  async list({ status = null, target_type = null, page = 1, page_size = DEFAULTS.PAGINATION.DEFAULT } = {}) {
    try {
      const result = await get(ENDPOINTS.REPORTS.LIST, {
        params: { status, target_type, page, page_size }
      })
      return {
        ok: true,
        reports: result.reports || [],
        total: result.total || 0,
        page: result.page || page,
        pageSize: result.pageSize || pageSize
      }
    } catch (err) {
      return { ok: false, error: err.message, reports: [], total: 0 }
    }
  },

  /**
   * Get report by ID (admin only)
   * @param {string} reportId
   * @returns {Promise<Object>}
   */
  async get(reportId) {
    try {
      const result = await get(ENDPOINTS.REPORTS.GET(reportId))
      return { ok: true, report: result.report }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Get report statistics (admin only)
   * @returns {Promise<Object>}
   */
  async getStats() {
    try {
      const result = await get(ENDPOINTS.REPORTS.STATS)
      return { ok: true, ...result }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Update/resolve a report (admin only)
   * @param {string} reportId
   * @param {Object} data
   * @param {string} [data.status]
   * @param {string} [data.resolution_note]
   * @param {string} [data.action_taken]
   * @returns {Promise<Object>}
   */
  async update(reportId, data) {
    try {
      const result = await put(ENDPOINTS.REPORTS.UPDATE(reportId), data)
      return { ok: true, report: result.report }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Delete a report (admin only)
   * @param {string} reportId
   * @returns {Promise<Object>}
   */
  async delete(reportId) {
    try {
      await del(ENDPOINTS.REPORTS.DELETE(reportId))
      return { ok: true }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }
}

export default reportsAPI
