/**
 * Alert History Operations
 *
 * S-Grade: Alert history query operations.
 * Single responsibility: Retrieve alert history.
 */

import { get } from '../client'
import { ENDPOINTS } from '../config'

/**
 * Get alert history
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>}
 */
export async function getHistory(params = {}) {
  try {
    const result = await get(ENDPOINTS.ALERTS.HISTORY, { params })

    return {
      ok: true,
      history: (result.history || []).map(h => ({
        id: h.id,
        ruleId: h.ruleId,
        ruleName: h.ruleName,
        severity: h.severity,
        message: h.message,
        workflowId: h.workflowId,
        workflowName: h.workflowName,
        triggeredAt: h.triggeredAt,
        resolvedAt: h.resolvedAt,
        resolution: h.resolution,
        metadata: h.metadata || {}
      })),
      pagination: {
        page: result.page || 1,
        limit: result.limit || 20,
        total: result.total || 0,
        totalPages: result.totalPages || 1
      }
    }
  } catch (err) {
    return {
      ok: false,
      error: err.message,
      history: [],
      pagination: { page: 1, limit: 20, total: 0, totalPages: 1 }
    }
  }
}
