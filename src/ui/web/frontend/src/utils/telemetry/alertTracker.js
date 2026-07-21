/**
 * Alert Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks alert events only.
 */

import { telemetry } from '@/services/telemetry'
import { ALERT_EVENTS } from '@/constants/telemetryEvents'

export const trackAlert = {
  acknowledge: (alertId, alertType) => {
    telemetry.track(ALERT_EVENTS.ACKNOWLEDGE, { alert_id: alertId, alert_type: alertType })
  },

  ruleCreate: (ruleType, conditions) => {
    telemetry.track(ALERT_EVENTS.RULE_CREATE, {
      rule_type: ruleType,
      conditions_count: Array.isArray(conditions) ? conditions.length : 1,
    })
  },

  ruleDelete: (ruleId) => {
    telemetry.track(ALERT_EVENTS.RULE_DELETE, { rule_id: ruleId })
  },
}
