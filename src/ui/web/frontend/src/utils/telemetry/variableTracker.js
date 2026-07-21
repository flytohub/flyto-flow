/**
 * Variable & Credential Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks variable and credential events only.
 */

import { telemetry } from '@/services/telemetry'
import { VARIABLE_EVENTS, CREDENTIAL_EVENTS } from '@/constants/telemetryEvents'

export const trackVariable = {
  create: (scope, isSecret) => {
    telemetry.track(VARIABLE_EVENTS.CREATE, { scope, is_secret: isSecret })
  },

  update: (variableId) => {
    telemetry.track(VARIABLE_EVENTS.UPDATE, { variable_id: variableId })
  },

  delete: (variableId) => {
    telemetry.track(VARIABLE_EVENTS.DELETE, { variable_id: variableId })
  },
}

export const trackCredential = {
  create: (scope) => {
    telemetry.track(CREDENTIAL_EVENTS.CREATE, { scope })
  },

  delete: (name) => {
    telemetry.track(CREDENTIAL_EVENTS.DELETE, { name })
  },

  reveal: (name, reason) => {
    telemetry.track(CREDENTIAL_EVENTS.REVEAL, { name, reason })
  },
}
