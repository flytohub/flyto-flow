/**
 * Dashboard API - Gateway API Access
 * Pure passthrough — all data processing is done server-side.
 */

import { get } from '@/api/client'
import { ENDPOINTS } from '@/api/config'

export const dashboardAPI = {
  async getStats() {
    try {
      const result = await get(ENDPOINTS.DASHBOARD.STATS)
      return {
        ok: true,
        stats: {
          sales: result.sales || 0,
          revenue: result.revenue || 0,
          published: result.published || 0,
          activeKeys: result.activeKeys || 0
        }
      }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  async getSalesTrend(days = 7) {
    try {
      const result = await get(ENDPOINTS.DASHBOARD.SALES_TREND, {
        params: { days }
      })
      return {
        ok: true,
        trend: result.trend || [],
        totalSales: result.totalSales || 0,
        totalRevenue: result.totalRevenue || 0,
        salesTrendPercent: result.salesTrendPercent || 0,
        revenueTrendPercent: result.revenueTrendPercent || 0
      }
    } catch (err) {
      return {
        ok: false, error: err.message,
        trend: [], totalSales: 0, totalRevenue: 0,
        salesTrendPercent: 0, revenueTrendPercent: 0
      }
    }
  },

  async getRecentActivity(activityLimit = 10) {
    try {
      const result = await get(ENDPOINTS.DASHBOARD.RECENT_ACTIVITY, {
        params: { limit: activityLimit }
      })
      return { ok: true, activities: result.activities || [] }
    } catch (err) {
      return { ok: false, error: err.message, activities: [] }
    }
  },

  async getMyPurchases(limitCount = 10) {
    try {
      const result = await get('/dashboard/my-purchases', {
        params: { limit: limitCount }
      })
      return {
        ok: true,
        purchases: result.purchases || [],
        totalSpent: result.totalSpent || 0,
        count: result.count || 0,
        freeCount: result.freeCount || 0
      }
    } catch (err) {
      return {
        ok: false, error: err.message,
        purchases: [], totalSpent: 0, count: 0, freeCount: 0
      }
    }
  }
}

export default dashboardAPI
