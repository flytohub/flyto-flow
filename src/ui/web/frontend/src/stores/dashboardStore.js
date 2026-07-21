/**
 * Dashboard Store
 * Manages dashboard state and data fetching.
 * All data processing is done server-side — store is a pure passthrough.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { dashboardAPI } from '@/api/dashboard'
import { telemetry } from '@/services/telemetry'

export const useDashboardStore = defineStore('dashboard', () => {
  // ========== State ==========
  const stats = ref({ sales: 0, revenue: 0, published: 0, activeKeys: 0 })
  const trend = ref([])
  const trendStats = ref({
    totalSales: 0, totalRevenue: 0,
    salesTrendPercent: 0, revenueTrendPercent: 0
  })
  const activities = ref([])
  const purchases = ref([])
  const purchaseStats = ref({ totalSpent: 0, count: 0, freeCount: 0 })
  const isLoading = ref(false)
  const error = ref(null)

  // Loading counter for parallel fetches
  let _pending = 0

  function _startFetch() {
    _pending++
    isLoading.value = true
  }

  function _endFetch() {
    _pending = Math.max(0, _pending - 1)
    if (_pending === 0) isLoading.value = false
  }

  // ========== Getters ==========
  const hasData = computed(() => stats.value.sales > 0 || stats.value.published > 0)

  // ========== Actions ==========
  async function fetchStats() {
    _startFetch()
    try {
      const result = await dashboardAPI.getStats()
      if (result.ok) stats.value = result.stats
      else error.value = result.error
      return result
    } catch (err) {
      error.value = err.message || 'Failed to fetch stats'
      return { ok: false, error: error.value }
    } finally {
      _endFetch()
    }
  }

  async function fetchTrend(days = 7) {
    _startFetch()
    try {
      const result = await dashboardAPI.getSalesTrend(days)
      if (result.ok) {
        trend.value = result.trend
        trendStats.value = {
          totalSales: result.totalSales,
          totalRevenue: result.totalRevenue,
          salesTrendPercent: result.salesTrendPercent,
          revenueTrendPercent: result.revenueTrendPercent,
        }
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to fetch trend'
      return { ok: false, error: error.value }
    } finally {
      _endFetch()
    }
  }

  async function fetchActivities(limit = 10) {
    _startFetch()
    try {
      const result = await dashboardAPI.getRecentActivity(limit)
      if (result.ok) activities.value = result.activities
      else error.value = result.error
      return result
    } catch (err) {
      error.value = err.message || 'Failed to fetch activities'
      return { ok: false, error: error.value }
    } finally {
      _endFetch()
    }
  }

  async function fetchPurchases(limit = 10) {
    _startFetch()
    try {
      const result = await dashboardAPI.getMyPurchases(limit)
      if (result.ok) {
        purchases.value = result.purchases
        purchaseStats.value = {
          totalSpent: result.totalSpent,
          count: result.count,
          freeCount: result.freeCount,
        }
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to fetch purchases'
      return { ok: false, error: error.value }
    } finally {
      _endFetch()
    }
  }

  async function fetchAll() {
    error.value = null
    try {
      await Promise.all([
        fetchStats(),
        fetchTrend(),
        fetchActivities(),
        fetchPurchases()
      ])
      telemetry.track('dashboard.load', {
        sales: stats.value.sales,
        published: stats.value.published
      })
    } catch (err) {
      error.value = err.message || 'Failed to fetch dashboard data'
    }
  }

  function clearError() {
    error.value = null
  }

  function reset() {
    stats.value = { sales: 0, revenue: 0, published: 0, activeKeys: 0 }
    trend.value = []
    trendStats.value = { totalSales: 0, totalRevenue: 0, salesTrendPercent: 0, revenueTrendPercent: 0 }
    activities.value = []
    purchases.value = []
    purchaseStats.value = { totalSpent: 0, count: 0, freeCount: 0 }
    isLoading.value = false
    error.value = null
    _pending = 0
  }

  return {
    // State
    stats, trend, trendStats, activities, purchases, purchaseStats,
    isLoading, error,
    // Getters
    hasData,
    // Actions
    fetchStats, fetchTrend, fetchActivities, fetchPurchases,
    fetchAll, clearError, reset
  }
})
