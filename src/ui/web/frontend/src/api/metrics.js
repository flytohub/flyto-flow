/**
 * Metrics API - Phase 8 Observability
 * Execution metrics and analytics data
 */

import { get } from '@/api/client'
import { ENDPOINTS } from '@/api/config'

export const metricsAPI = {
  /**
   * Get metrics summary (total executions, success rate, etc.)
   * @param {string} range - Time range (e.g., '7d', '30d', '24h')
   * @returns {Promise<Object>} Summary stats
   */
  async getSummary(range = '7d') {
    try {
      const result = await get(ENDPOINTS.METRICS.SUMMARY, {
        params: { range }
      })

      return {
        ok: true,
        summary: {
          totalExecutions: result.totalExecutions || 0,
          successful: result.successful || 0,
          failed: result.failed || 0,
          successRate: result.successRate || 0,
          avgDurationMs: result.avgDurationMs || 0,
          // Comparison with previous period
          executionsChange: result.executionsChange || 0,
          successRateChange: result.successRateChange || 0,
          durationChange: result.durationChange || 0,
          failuresChange: result.failuresChange || 0
        }
      }
    } catch (err) {
      return {
        ok: false,
        error: err.message,
        summary: {
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
      }
    }
  },

  /**
   * Get execution trend data for charts
   * @param {string} range - Time range (e.g., '7d', '30d')
   * @returns {Promise<Object>} Trend data points
   */
  async getTrend(range = '7d') {
    try {
      const result = await get(ENDPOINTS.METRICS.TREND, {
        params: { range }
      })

      return {
        ok: true,
        trend: (result.trend || []).map(point => ({
          date: point.date,
          label: point.label || point.date,
          successful: point.successful || 0,
          failed: point.failed || 0,
          total: point.total || 0
        }))
      }
    } catch (err) {
      // Return empty trend on error
      return { ok: false, error: err.message, trend: [] }
    }
  },

  /**
   * Get top workflows by execution count
   * @param {number} limit - Number of workflows to return
   * @param {string} range - Time range
   * @returns {Promise<Object>} Top workflows list
   */
  async getTopWorkflows(limit = 5, range = '7d') {
    try {
      const result = await get(ENDPOINTS.METRICS.TOP_WORKFLOWS, {
        params: { limit, range }
      })

      return {
        ok: true,
        workflows: (result.workflows || []).map(w => ({
          id: w.id,
          name: w.name,
          executions: w.executions || 0,
          successRate: w.successRate || 0,
          avgDurationMs: w.avgDurationMs || 0
        }))
      }
    } catch (err) {
      return { ok: false, error: err.message, workflows: [] }
    }
  },

  /**
   * Get recent failed executions
   * @param {number} limit - Number of failures to return
   * @returns {Promise<Object>} Recent failures list
   */
  async getRecentFailures(limit = 5) {
    try {
      const result = await get(ENDPOINTS.METRICS.RECENT_FAILURES, {
        params: { limit }
      })

      return {
        ok: true,
        failures: (result.failures || []).map(f => ({
          executionId: f.executionId,
          workflowId: f.workflowId,
          workflowName: f.workflowName,
          error: f.error,
          failedAt: f.failedAt,
          durationMs: f.durationMs
        }))
      }
    } catch (err) {
      return { ok: false, error: err.message, failures: [] }
    }
  },

  /**
   * Export metrics in specified format
   * @param {string} format - Export format ('prometheus', 'json', 'csv')
   * @param {string} range - Time range
   * @returns {Promise<Object>} Exported data
   */
  async exportMetrics(format = 'json', range = '7d') {
    try {
      const result = await get(ENDPOINTS.METRICS.EXPORT, {
        params: { format, range }
      })

      return {
        ok: true,
        data: result.data,
        format: format
      }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }
}

export default metricsAPI
