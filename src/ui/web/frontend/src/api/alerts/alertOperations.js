/**
 * Alert Operations
 *
 * S-Grade: Alert CRUD and action operations.
 * Single responsibility: Manage active alerts.
 */

import { get, post } from '../client'
import { ENDPOINTS } from '../config'
import i18n from '@/i18n'

/**
 * Get active alerts
 * @returns {Promise<Object>}
 */
export async function getActiveAlerts() {
  try {
    const result = await get(ENDPOINTS.ALERTS.LIST)

    return {
      ok: true,
      alerts: (result.alerts || []).map(a => ({
        id: a.id,
        ruleId: a.ruleId,
        ruleName: a.ruleName,
        severity: a.severity || 'warning',
        message: a.message,
        workflowId: a.workflowId,
        workflowName: a.workflowName,
        triggeredAt: a.triggeredAt,
        acknowledged: a.acknowledged || false,
        acknowledgedAt: a.acknowledgedAt,
        acknowledgedBy: a.acknowledgedBy,
        metadata: a.metadata || {}
      })),
      // S-Grade: Backend-computed counts (camelCase)
      activeCount: result.activeCount,
      criticalCount: result.criticalCount,
      warningCount: result.warningCount
    }
  } catch (err) {
    return { ok: false, error: err.message, alerts: [] }
  }
}

/**
 * Get single alert by ID
 * @param {string} alertId - Alert ID
 * @returns {Promise<Object>}
 */
export async function getAlert(alertId) {
  try {
    const result = await get(ENDPOINTS.ALERTS.GET(alertId))

    return {
      ok: true,
      alert: {
        id: result.id,
        ruleId: result.ruleId,
        ruleName: result.ruleName,
        severity: result.severity || 'warning',
        message: result.message,
        workflowId: result.workflowId,
        workflowName: result.workflowName,
        triggeredAt: result.triggeredAt,
        acknowledged: result.acknowledged || false,
        acknowledgedAt: result.acknowledgedAt,
        acknowledgedBy: result.acknowledgedBy,
        metadata: result.metadata || {}
      }
    }
  } catch (err) {
    return { ok: false, error: err.message, alert: null }
  }
}

/**
 * Acknowledge an alert
 * @param {string} alertId - Alert ID
 * @returns {Promise<Object>}
 */
export async function acknowledgeAlert(alertId) {
  try {
    const result = await post(ENDPOINTS.ALERTS.ACKNOWLEDGE(alertId))
    return { ok: true, message: result.message || i18n.global.t('message.alertAcknowledged') }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Mute an alert
 * @param {string} alertId - Alert ID
 * @param {number} duration - Mute duration in minutes
 * @returns {Promise<Object>}
 */
export async function muteAlert(alertId, duration = 60) {
  try {
    const result = await post(ENDPOINTS.ALERTS.MUTE(alertId), { duration })
    return { ok: true, message: result.message || i18n.global.t('message.alertMuted') }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}
