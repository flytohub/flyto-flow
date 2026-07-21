/**
 * Alert Rule Operations
 *
 * S-Grade: Alert rule CRUD operations.
 * Single responsibility: Manage alert rules.
 */

import { get, post, put, del } from '../client'
import { ENDPOINTS } from '../config'

/**
 * Transform rule data from API response
 * @param {Object} r - Raw rule data
 * @returns {Object} Transformed rule
 */
function transformRule(r) {
  return {
    id: r.id,
    name: r.name,
    description: r.description,
    enabled: r.enabled !== false,
    condition: {
      type: r.condition?.type || 'failure_rate',
      operator: r.condition?.operator || 'gt',
      threshold: r.condition?.threshold || 0
    },
    scope: r.scope || 'all',
    workflowIds: r.workflowIds || [],
    severity: r.severity || 'warning',
    notifications: r.notifications || [],
    cooldownMinutes: r.cooldownMinutes || 15,
    createdAt: r.createdAt,
    updatedAt: r.updatedAt
  }
}

/**
 * Get alert rules
 * @returns {Promise<Object>}
 */
export async function getRules() {
  try {
    const result = await get(ENDPOINTS.ALERTS.RULES)

    return {
      ok: true,
      rules: (result.rules || []).map(transformRule),
      // S-Grade: Backend-computed counts
      enabledCount: result.enabledCount,
      totalCount: result.totalCount
    }
  } catch (err) {
    return { ok: false, error: err.message, rules: [] }
  }
}

/**
 * Create a new alert rule
 * @param {Object} ruleData - Rule configuration
 * @returns {Promise<Object>}
 */
export async function createRule(ruleData) {
  try {
    const result = await post(ENDPOINTS.ALERTS.RULES, ruleData)

    return {
      ok: true,
      rule: transformRule(result)
    }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Update an alert rule
 * @param {string} ruleId - Rule ID
 * @param {Object} ruleData - Updated rule configuration
 * @returns {Promise<Object>}
 */
export async function updateRule(ruleId, ruleData) {
  try {
    const result = await put(ENDPOINTS.ALERTS.RULE(ruleId), ruleData)

    return {
      ok: true,
      rule: transformRule(result)
    }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Delete an alert rule
 * @param {string} ruleId - Rule ID
 * @returns {Promise<Object>}
 */
export async function deleteRule(ruleId) {
  try {
    await del(ENDPOINTS.ALERTS.RULE(ruleId))
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}
