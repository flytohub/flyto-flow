/**
 * Creator Dashboard API
 * Handle creator analytics and stats
 */

import { get, post } from '@/api/client'
import { ENDPOINTS } from '@/api/config'

export const creatorAPI = {
  /**
   * Get regional sales statistics
   */
  async getRegionalStats(period = '30d') {
    try {
      const result = await get(ENDPOINTS.CREATOR.STATS_REGIONAL, {
        params: { period }
      })
      return {
        ok: result.ok !== false,
        regionalStats: result.regionalStats || [],
        totalSales: result.totalSales || 0,
        totalRevenue: result.totalRevenue || 0,
        period: result.period || period
      }
    } catch (err) {
      return {
        ok: false,
        error: err.message,
        regionalStats: [],
        totalSales: 0,
        totalRevenue: 0
      }
    }
  },

  /**
   * Get overview statistics
   */
  async getOverviewStats() {
    try {
      const result = await get(ENDPOINTS.CREATOR.STATS_OVERVIEW)
      return {
        ok: result.ok !== false,
        stats: result.stats || {}
      }
    } catch (err) {
      return { ok: false, error: err.message, stats: {} }
    }
  },

  /**
   * Get per-template statistics
   */
  async getTemplateStats(page = 1, pageSize = 10) {
    try {
      const result = await get(ENDPOINTS.CREATOR.STATS_TEMPLATES, {
        params: { page, pageSize }
      })
      return {
        ok: result.ok !== false,
        templates: result.templates || [],
        total: result.total || 0,
        page: result.page || page,
        pageSize: result.pageSize || pageSize
      }
    } catch (err) {
      return {
        ok: false,
        error: err.message,
        templates: [],
        total: 0
      }
    }
  },

  /**
   * Submit a translation for review
   */
  async submitTranslation(data) {
    try {
      const result = await post(ENDPOINTS.TRANSLATION_REVIEWS.SUBMIT, data)
      return {
        ok: result.ok !== false,
        review: result.review,
        message: result.message
      }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Get my submitted translations
   */
  async getMyTranslations(page = 1, pageSize = 20) {
    try {
      const result = await get(ENDPOINTS.TRANSLATION_REVIEWS.MY, {
        params: { page, pageSize }
      })
      return {
        ok: result.ok !== false,
        reviews: result.reviews || [],
        total: result.total || 0
      }
    } catch (err) {
      return { ok: false, error: err.message, reviews: [], total: 0 }
    }
  }
}

export default creatorAPI
