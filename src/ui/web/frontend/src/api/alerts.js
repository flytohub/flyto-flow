/**
 * Alerts API
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All alerts API logic split into alerts/* directory.
 *
 * Split modules:
 * - alerts/alertOperations.js: Alert CRUD and actions
 * - alerts/ruleOperations.js: Alert rule management
 * - alerts/historyOperations.js: Alert history queries
 */

// Re-export all from split modules
export {
  getActiveAlerts,
  getAlert,
  acknowledgeAlert,
  muteAlert,
  getRules,
  createRule,
  updateRule,
  deleteRule,
  getHistory,
  alertsAPI
} from './alerts/index'

export { default } from './alerts/index'
