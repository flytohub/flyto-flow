/**
 * Metrics Store - Phase 8 Observability
 * Manages execution metrics state and data fetching
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { metricsAPI } from '@/api/metrics'
import { formatDuration } from '@/utils/format'

export const useMetricsStore = defineStore('metrics', () => {
  // ========== State ==========
  const summary = ref({
    totalExecutions: 0,
    successful: 0,
    failed: 0,
    successRate: 0,
    avgDurationMs: 0,
    executionsChange: 0,
    successRateChange: 0,
    durationChange: 0,
    failuresChange: 0
  })
  const trend = ref([])
  const topWorkflows = ref([])
  const recentFailures = ref([])
  const timeRange = ref('7d')
  const isLoading = ref(false)
  const error = ref(null)

  // ========== Getters ==========
  const totalExecutions = computed(() => summary.value.totalExecutions)
  const successRate = computed(() => summary.value.successRate)
  const avgDuration = computed(() => summary.value.avgDurationMs)
  const failedCount = computed(() => summary.value.failed)
  const hasData = computed(() => summary.value.totalExecutions > 0)

  // Format duration for display
  const formattedAvgDuration = computed(() => formatDuration(summary.value.avgDurationMs))

  // ========== Actions ==========

  /**
   * Fetch metrics summary
   * @param {string} range - Time range
   * @returns {Promise<Object>} Summary result
   */
  async function fetchSummary(range = timeRange.value) {
    isLoading.value = true
    error.value = null

    try {
      const result = await metricsAPI.getSummary(range)
      if (result.ok) {
        summary.value = result.summary
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to fetch metrics summary'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch execution trend data
   * @param {string} range - Time range
   * @returns {Promise<Object>} Trend result
   */
  async function fetchTrend(range = timeRange.value) {
    isLoading.value = true
    error.value = null

    try {
      const result = await metricsAPI.getTrend(range)
      if (result.ok) {
        trend.value = result.trend
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to fetch trend data'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch top workflows
   * @param {number} limit - Number of workflows to fetch
   * @param {string} range - Time range
   * @returns {Promise<Object>} Top workflows result
   */
  async function fetchTopWorkflows(limit = 5, range = timeRange.value) {
    isLoading.value = true
    error.value = null

    try {
      const result = await metricsAPI.getTopWorkflows(limit, range)
      if (result.ok) {
        topWorkflows.value = result.workflows
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to fetch top workflows'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch recent failures
   * @param {number} limit - Number of failures to fetch
   * @returns {Promise<Object>} Recent failures result
   */
  async function fetchRecentFailures(limit = 5) {
    isLoading.value = true
    error.value = null

    try {
      const result = await metricsAPI.getRecentFailures(limit)
      if (result.ok) {
        recentFailures.value = result.failures
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to fetch recent failures'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch all metrics data at once
   * @param {string} range - Time range
   * @returns {Promise<void>}
   */
  async function fetchAll(range = timeRange.value) {
    isLoading.value = true
    error.value = null
    timeRange.value = range

    try {
      await Promise.all([
        fetchSummary(range),
        fetchTrend(range),
        fetchTopWorkflows(5, range),
        fetchRecentFailures(5)
      ])
    } catch (err) {
      error.value = err.message || 'Failed to fetch metrics data'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Set time range and refresh data
   * @param {string} range - New time range
   */
  async function setTimeRange(range) {
    timeRange.value = range
    await fetchAll(range)
  }

  /**
   * Clear error
   */
  function clearError() {
    error.value = null
  }

  /**
   * Reset state
   */
  function reset() {
    summary.value = {
      totalExecutions: 0,
      successful: 0,
      failed: 0,
      successRate: 0,
      avgDurationMs: 0,
      executionsChange: 0,
      successRateChange: 0,
      durationChange: 0,
      failuresChange: 0
    }
    trend.value = []
    topWorkflows.value = []
    recentFailures.value = []
    timeRange.value = '7d'
    isLoading.value = false
    error.value = null
  }

  return {
    // State
    summary,
    trend,
    topWorkflows,
    recentFailures,
    timeRange,
    isLoading,
    error,

    // Getters
    totalExecutions,
    successRate,
    avgDuration,
    failedCount,
    hasData,
    formattedAvgDuration,

    // Actions
    fetchSummary,
    fetchTrend,
    fetchTopWorkflows,
    fetchRecentFailures,
    fetchAll,
    setTimeRange,
    clearError,
    reset
  }
})
