/**
 * Alert State Helpers
 *
 * S-Grade: State update utilities for alert store.
 * Single responsibility: State mutations and updates.
 */

/**
 * Default pagination state
 */
export const DEFAULT_PAGINATION = {
  page: 1,
  limit: 20,
  total: 0,
  totalPages: 1
}

/**
 * Update alert counts from API response
 * @param {Object} refs - Count refs object
 * @param {Object} result - API response
 */
export function updateAlertCounts(refs, result) {
  if (result.activeCount !== undefined) {
    refs.activeCount.value = result.activeCount
  }
  if (result.criticalCount !== undefined) {
    refs.criticalCount.value = result.criticalCount
  }
  if (result.warningCount !== undefined) {
    refs.warningCount.value = result.warningCount
  }
}

/**
 * Update rule counts from API response
 * @param {Object} refs - Count refs object
 * @param {Object} result - API response
 */
export function updateRuleCounts(refs, result) {
  if (result.enabledCount !== undefined) {
    refs.enabledRulesCount.value = result.enabledCount
  }
  if (result.totalCount !== undefined) {
    refs.totalRulesCount.value = result.totalCount
  }
}

/**
 * Mark alert as acknowledged in local state
 * @param {Array} alerts - Alerts array
 * @param {string} alertId - Alert ID
 */
export function markAlertAcknowledged(alerts, alertId) {
  const index = alerts.findIndex(a => a.id === alertId)
  if (index !== -1) {
    alerts[index].acknowledged = true
    alerts[index].acknowledgedAt = new Date().toISOString()
  }
}

/**
 * Update rule in local state
 * @param {Array} rules - Rules array
 * @param {string} ruleId - Rule ID
 * @param {Object} updatedRule - Updated rule data
 */
export function updateRuleInList(rules, ruleId, updatedRule) {
  const index = rules.findIndex(r => r.id === ruleId)
  if (index !== -1) {
    rules[index] = updatedRule
  }
}

/**
 * Remove item from array by ID
 * @param {Array} items - Items array
 * @param {string} itemId - Item ID to remove
 */
export function removeById(items, itemId) {
  const index = items.findIndex(item => item.id === itemId)
  if (index !== -1) {
    items.splice(index, 1)
  }
}

/**
 * Reset all alert state
 * @param {Object} state - State object with all refs
 */
export function resetAlertState(state) {
  state.activeAlerts.value = []
  state.rules.value = []
  state.history.value = []
  state.pagination.value = { ...DEFAULT_PAGINATION }
  state.isLoading.value = false
  state.isLoadingRules.value = false
  state.error.value = null
  state.activeCount.value = 0
  state.criticalCount.value = 0
  state.warningCount.value = 0
  state.enabledRulesCount.value = 0
  state.totalRulesCount.value = 0
}
