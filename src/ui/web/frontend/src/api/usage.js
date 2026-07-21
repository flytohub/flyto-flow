/**
 * Usage API Client
 *
 * Client for querying usage/metering data.
 * Pro feature - tracks points consumption.
 */

import { get } from '@/api/client'

/**
 * Get current billing period usage
 * @returns {Promise<{ok: boolean, totalPoints: number, pointsLimit: number|null, pointsRemaining: number|null, periodStart: string, periodEnd: string, byModule: Array}>}
 */
export async function getCurrentUsage() {
  return await get('/usage/current')
}

/**
 * Get usage history
 * @param {Object} options
 * @param {string} options.period - Time period (day, week, month)
 * @param {number} options.limit - Number of periods to return
 * @returns {Promise<{ok: boolean, history: Array, totalPeriods: number}>}
 */
export async function getUsageHistory({ period = 'month', limit = 6 } = {}) {
  return await get('/usage/history', {
    params: { period, limit }
  })
}

/**
 * Get usage details for a specific execution
 * @param {string} executionId - Execution ID
 * @returns {Promise<{ok: boolean, executionId: string, totalPoints: number, records: Array}>}
 */
export async function getExecutionUsage(executionId) {
  return await get(`/usage/execution/${executionId}`)
}

/**
 * Get per-feature quota usage for current user (Free plan)
 * @returns {Promise<{ok: boolean, plan: string, quotas: Object}>}
 */
export async function getFeatureQuotas() {
  return await get('/usage/feature-quotas')
}

export default {
  getCurrentUsage,
  getUsageHistory,
  getExecutionUsage,
  getFeatureQuotas,
}
