import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/client', () => ({
  get: vi.fn()
}))

vi.mock('@/api/config', () => ({
  ENDPOINTS: {
    DASHBOARD: {
      STATS: '/dashboard/stats',
      SALES_TREND: '/dashboard/sales-trend',
      RECENT_ACTIVITY: '/dashboard/recent-activity'
    }
  }
}))

import { get } from '@/api/client'
import { dashboardAPI } from '@/api/dashboard'

describe('Dashboard API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // =========================================================================
  // getStats
  // =========================================================================

  describe('getStats()', () => {
    it('calls GET /dashboard/stats and wraps result', async () => {
      get.mockResolvedValue({ sales: 100, revenue: 5000, published: 10, activeKeys: 5 })

      const result = await dashboardAPI.getStats()

      expect(get).toHaveBeenCalledWith('/dashboard/stats')
      expect(result.ok).toBe(true)
      expect(result.stats).toEqual({
        sales: 100,
        revenue: 5000,
        published: 10,
        activeKeys: 5
      })
    })

    it('returns zero defaults for missing fields', async () => {
      get.mockResolvedValue({})

      const result = await dashboardAPI.getStats()

      expect(result.stats.sales).toBe(0)
      expect(result.stats.revenue).toBe(0)
      expect(result.stats.published).toBe(0)
      expect(result.stats.activeKeys).toBe(0)
    })

    it('returns error on failure', async () => {
      get.mockRejectedValue(new Error('Unauthorized'))

      const result = await dashboardAPI.getStats()

      expect(result.ok).toBe(false)
      expect(result.error).toBe('Unauthorized')
    })
  })

  // =========================================================================
  // getSalesTrend
  // =========================================================================

  describe('getSalesTrend()', () => {
    it('calls GET /dashboard/sales-trend with days param', async () => {
      get.mockResolvedValue({
        trend: [{ date: '2026-03-20', sales: 5 }],
        totalSales: 50,
        totalRevenue: 2500,
        salesTrendPercent: 12,
        revenueTrendPercent: 8
      })

      const result = await dashboardAPI.getSalesTrend(30)

      expect(get).toHaveBeenCalledWith('/dashboard/sales-trend', {
        params: { days: 30 }
      })
      expect(result.ok).toBe(true)
      expect(result.trend).toHaveLength(1)
      expect(result.totalSales).toBe(50)
      expect(result.salesTrendPercent).toBe(12)
    })

    it('defaults to 7 days', async () => {
      get.mockResolvedValue({ trend: [] })

      await dashboardAPI.getSalesTrend()

      expect(get).toHaveBeenCalledWith('/dashboard/sales-trend', {
        params: { days: 7 }
      })
    })

    it('returns zero defaults on error', async () => {
      get.mockRejectedValue(new Error('fail'))

      const result = await dashboardAPI.getSalesTrend()

      expect(result.ok).toBe(false)
      expect(result.trend).toEqual([])
      expect(result.totalSales).toBe(0)
      expect(result.totalRevenue).toBe(0)
      expect(result.salesTrendPercent).toBe(0)
      expect(result.revenueTrendPercent).toBe(0)
    })
  })

  // =========================================================================
  // getRecentActivity
  // =========================================================================

  describe('getRecentActivity()', () => {
    it('calls GET /dashboard/recent-activity with limit param', async () => {
      get.mockResolvedValue({ activities: [{ type: 'sale', id: 'a1' }] })

      const result = await dashboardAPI.getRecentActivity(5)

      expect(get).toHaveBeenCalledWith('/dashboard/recent-activity', {
        params: { limit: 5 }
      })
      expect(result.ok).toBe(true)
      expect(result.activities).toHaveLength(1)
    })

    it('defaults limit to 10', async () => {
      get.mockResolvedValue({ activities: [] })

      await dashboardAPI.getRecentActivity()

      expect(get).toHaveBeenCalledWith('/dashboard/recent-activity', {
        params: { limit: 10 }
      })
    })

    it('returns empty activities on error', async () => {
      get.mockRejectedValue(new Error('fail'))

      const result = await dashboardAPI.getRecentActivity()

      expect(result.activities).toEqual([])
    })
  })

  // =========================================================================
  // getMyPurchases
  // =========================================================================

  describe('getMyPurchases()', () => {
    it('calls GET /dashboard/my-purchases with limit param', async () => {
      get.mockResolvedValue({
        purchases: [{ id: 'p1' }],
        totalSpent: 1000,
        count: 5,
        freeCount: 3
      })

      const result = await dashboardAPI.getMyPurchases(5)

      expect(get).toHaveBeenCalledWith('/dashboard/my-purchases', {
        params: { limit: 5 }
      })
      expect(result.ok).toBe(true)
      expect(result.purchases).toHaveLength(1)
      expect(result.totalSpent).toBe(1000)
      expect(result.count).toBe(5)
      expect(result.freeCount).toBe(3)
    })

    it('returns zero defaults on error', async () => {
      get.mockRejectedValue(new Error('fail'))

      const result = await dashboardAPI.getMyPurchases()

      expect(result.ok).toBe(false)
      expect(result.purchases).toEqual([])
      expect(result.totalSpent).toBe(0)
      expect(result.count).toBe(0)
      expect(result.freeCount).toBe(0)
    })
  })
})
