/**
 * Usage Store
 *
 * Manages usage/metering state for Pro users.
 * Tracks points consumption and provides computed values for UI.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as usageAPI from '@/api/usage'

export const useUsageStore = defineStore('usage', () => {
  // ========== State ==========
  const currentUsage = ref(null)
  const usageHistory = ref([])
  const featureQuotas = ref(null)     // Free user per-feature quotas
  const isLoading = ref(false)
  const error = ref(null)
  const lastFetched = ref(null)
  const quotasFetched = ref(null)

  // Cache TTL (5 minutes)
  const CACHE_TTL = 5 * 60 * 1000

  // ========== Getters ==========

  /** Total points used this period */
  const totalPoints = computed(() => currentUsage.value?.totalPoints ?? 0)

  /** Points limit (null = unlimited) */
  const pointsLimit = computed(() => currentUsage.value?.pointsLimit ?? null)

  /** Points remaining (null = unlimited) — computed by backend */
  const pointsRemaining = computed(() => currentUsage.value?.pointsRemaining ?? null)

  /** Usage percentage (0-100, null if unlimited) — computed by backend */
  const usagePercentage = computed(() => currentUsage.value?.usagePercentage ?? null)

  /** Is usage near limit (>80%)? — computed by backend */
  const isNearLimit = computed(() => currentUsage.value?.isNearLimit ?? false)

  /** Is usage at or over limit? — computed by backend */
  const isOverLimit = computed(() => currentUsage.value?.isOverLimit ?? false)

  /** Current billing period */
  const billingPeriod = computed(() => ({
    start: currentUsage.value?.periodStart ?? null,
    end: currentUsage.value?.periodEnd ?? null,
  }))

  /** Usage breakdown by module */
  const byModule = computed(() => currentUsage.value?.byModule ?? [])

  /** Top 5 modules by usage — pre-sorted by backend */
  const topModules = computed(() => currentUsage.value?.topModules ?? [])

  /** Formatted points display — computed by backend */
  const formattedUsage = computed(() => currentUsage.value?.formattedUsage ?? '0')

  /** Formatted limit display — computed by backend */
  const formattedLimit = computed(() => currentUsage.value?.formattedLimit ?? 'Unlimited')

  // ========== Actions ==========

  /**
   * Fetch current usage (with caching)
   * @param {boolean} force - Force refresh, ignoring cache
   */
  async function fetchCurrentUsage(force = false) {
    // Check cache
    if (!force && lastFetched.value && currentUsage.value) {
      const elapsed = Date.now() - lastFetched.value
      if (elapsed < CACHE_TTL) {
        return currentUsage.value
      }
    }

    isLoading.value = true
    error.value = null

    try {
      const result = await usageAPI.getCurrentUsage()

      if (result) {
        currentUsage.value = {
          totalPoints: result.totalPoints ?? 0,
          pointsLimit: result.pointsLimit,
          pointsRemaining: result.pointsRemaining,
          usagePercentage: result.usagePercentage ?? null,
          isNearLimit: result.isNearLimit ?? false,
          isOverLimit: result.isOverLimit ?? false,
          formattedUsage: result.formattedUsage ?? '0',
          formattedLimit: result.formattedLimit ?? 'Unlimited',
          periodStart: result.periodStart,
          periodEnd: result.periodEnd,
          byModule: result.byModule ?? [],
          topModules: result.topModules ?? [],
        }
        lastFetched.value = Date.now()
      }

      return currentUsage.value
    } catch (err) {
      error.value = err.userMessage || err.message || 'Failed to fetch usage'
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch usage history
   * @param {Object} options
   * @param {string} options.period - Time period (day, week, month)
   * @param {number} options.limit - Number of periods
   */
  async function fetchHistory({ period = 'month', limit = 6 } = {}) {
    isLoading.value = true
    error.value = null

    try {
      const result = await usageAPI.getUsageHistory({ period, limit })

      if (result?.history) {
        usageHistory.value = result.history
      }

      return result?.history ?? []
    } catch (err) {
      error.value = err.userMessage || err.message || 'Failed to fetch history'
      return []
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get usage for a specific execution
   * @param {string} executionId
   */
  async function fetchExecutionUsage(executionId) {
    try {
      return await usageAPI.getExecutionUsage(executionId)
    } catch (err) {
      console.error('Failed to fetch execution usage:', err)
      return null
    }
  }

  /**
   * Fetch per-feature quotas for Free users (with caching)
   * @param {boolean} force - Force refresh
   */
  async function fetchFeatureQuotas(force = false) {
    if (!force && quotasFetched.value && featureQuotas.value) {
      const elapsed = Date.now() - quotasFetched.value
      if (elapsed < CACHE_TTL) return featureQuotas.value
    }

    try {
      const result = await usageAPI.getFeatureQuotas()
      if (result?.ok) {
        featureQuotas.value = result.quotas || {}
        quotasFetched.value = Date.now()
      }
      return featureQuotas.value
    } catch (err) {
      console.error('Failed to fetch feature quotas:', err)
      return null
    }
  }

  /**
   * Clear cache and reset state
   */
  function reset() {
    currentUsage.value = null
    usageHistory.value = []
    featureQuotas.value = null
    lastFetched.value = null
    quotasFetched.value = null
    error.value = null
  }

  /**
   * Invalidate cache (force next fetch to refresh)
   */
  function invalidateCache() {
    lastFetched.value = null
    quotasFetched.value = null
  }

  return {
    // State
    currentUsage,
    usageHistory,
    featureQuotas,
    isLoading,
    error,

    // Getters
    totalPoints,
    pointsLimit,
    pointsRemaining,
    usagePercentage,
    isNearLimit,
    isOverLimit,
    billingPeriod,
    byModule,
    topModules,
    formattedUsage,
    formattedLimit,

    // Actions
    fetchCurrentUsage,
    fetchHistory,
    fetchExecutionUsage,
    fetchFeatureQuotas,
    reset,
    invalidateCache,
  }
})
