/**
 * Alerts API Module
 *
 * S-Grade: Re-export all alerts API functionality.
 *
 * Split modules:
 * - alertOperations.js: Alert CRUD and actions
 * - ruleOperations.js: Alert rule management
 * - historyOperations.js: Alert history queries
 */

// Alert operations
export {
  getActiveAlerts,
  getAlert,
  acknowledgeAlert,
  muteAlert
} from './alertOperations'

// Rule operations
export {
  getRules,
  createRule,
  updateRule,
  deleteRule
} from './ruleOperations'

// History operations
export { getHistory } from './historyOperations'

// Aggregate API object
import { getActiveAlerts, getAlert, acknowledgeAlert, muteAlert } from './alertOperations'
import { getRules, createRule, updateRule, deleteRule } from './ruleOperations'
import { getHistory } from './historyOperations'

export const alertsAPI = {
  getActiveAlerts,
  getAlert,
  acknowledgeAlert,
  muteAlert,
  getRules,
  createRule,
  updateRule,
  deleteRule,
  getHistory
}

export default alertsAPI
