/**
 * Alerts Store - Split Modules Re-exports
 *
 * S-Grade: Centralized exports for alerts functionality.
 *
 * Split structure:
 * - alertApiHelpers.js: API call wrappers (~110 lines)
 * - alertStateHelpers.js: State update utilities (~100 lines)
 * - alertStoreCore.js: Main store (~180 lines)
 */

// Main store
export { useAlertStore } from './alertStoreCore'

// Helpers for advanced use
export {
  fetchActiveAlertsApi,
  acknowledgeAlertApi,
  muteAlertApi,
  fetchRulesApi,
  createRuleApi,
  updateRuleApi,
  deleteRuleApi,
  fetchHistoryApi
} from './alertApiHelpers'

export {
  DEFAULT_PAGINATION,
  updateAlertCounts,
  updateRuleCounts,
  markAlertAcknowledged,
  updateRuleInList,
  removeById,
  resetAlertState
} from './alertStateHelpers'
