/**
 * Alert API Helpers
 *
 * S-Grade: Wraps API calls with standardized error handling.
 * Single responsibility: API communication for alerts.
 */

import { alertsAPI } from '@/api/alerts'

/**
 * Execute API call with error handling
 * @param {Function} apiCall - API function to execute
 * @param {string} errorMessage - Default error message
 * @returns {Promise<Object>} API result
 */
async function executeApiCall(apiCall, errorMessage) {
  try {
    const result = await apiCall()
    return result.ok ? result : { ok: false, error: result.error }
  } catch (err) {
    return { ok: false, error: err.message || errorMessage }
  }
}

/**
 * Fetch active alerts from API
 * @returns {Promise<Object>}
 */
export async function fetchActiveAlertsApi() {
  return executeApiCall(
    () => alertsAPI.getActiveAlerts(),
    'Failed to fetch active alerts'
  )
}

/**
 * Acknowledge an alert
 * @param {string} alertId - Alert ID
 * @returns {Promise<Object>}
 */
export async function acknowledgeAlertApi(alertId) {
  return executeApiCall(
    () => alertsAPI.acknowledgeAlert(alertId),
    'Failed to acknowledge alert'
  )
}

/**
 * Mute an alert
 * @param {string} alertId - Alert ID
 * @param {number} duration - Duration in minutes
 * @returns {Promise<Object>}
 */
export async function muteAlertApi(alertId, duration) {
  return executeApiCall(
    () => alertsAPI.muteAlert(alertId, duration),
    'Failed to mute alert'
  )
}

/**
 * Fetch alert rules from API
 * @returns {Promise<Object>}
 */
export async function fetchRulesApi() {
  return executeApiCall(
    () => alertsAPI.getRules(),
    'Failed to fetch alert rules'
  )
}

/**
 * Create a new alert rule
 * @param {Object} ruleData - Rule configuration
 * @returns {Promise<Object>}
 */
export async function createRuleApi(ruleData) {
  return executeApiCall(
    () => alertsAPI.createRule(ruleData),
    'Failed to create alert rule'
  )
}

/**
 * Update an alert rule
 * @param {string} ruleId - Rule ID
 * @param {Object} ruleData - Updated configuration
 * @returns {Promise<Object>}
 */
export async function updateRuleApi(ruleId, ruleData) {
  return executeApiCall(
    () => alertsAPI.updateRule(ruleId, ruleData),
    'Failed to update alert rule'
  )
}

/**
 * Delete an alert rule
 * @param {string} ruleId - Rule ID
 * @returns {Promise<Object>}
 */
export async function deleteRuleApi(ruleId) {
  return executeApiCall(
    () => alertsAPI.deleteRule(ruleId),
    'Failed to delete alert rule'
  )
}

/**
 * Fetch alert history
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>}
 */
export async function fetchHistoryApi(params) {
  return executeApiCall(
    () => alertsAPI.getHistory(params),
    'Failed to fetch alert history'
  )
}
