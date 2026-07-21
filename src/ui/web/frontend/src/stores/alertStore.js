/**
 * Alert Store
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All functionality split into stores/alerts/* directory.
 *
 * Split modules:
 * - alerts/alertApiHelpers.js: API call wrappers
 * - alerts/alertStateHelpers.js: State update utilities
 * - alerts/alertStoreCore.js: Main store
 */

// Re-export store
export { useAlertStore } from './alerts'

// Re-export helpers for advanced use
export {
  DEFAULT_PAGINATION,
  updateAlertCounts,
  updateRuleCounts,
  markAlertAcknowledged,
  updateRuleInList,
  removeById,
  resetAlertState
} from './alerts'
