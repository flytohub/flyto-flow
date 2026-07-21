/**
 * Auth Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks auth events only.
 */

import { telemetry } from '@/services/telemetry'
import { AUTH_EVENTS } from '@/constants/telemetryEvents'

export const trackAuth = {
  login: (method = 'email') => {
    telemetry.track(AUTH_EVENTS.LOGIN, { method })
  },

  logout: () => {
    telemetry.track(AUTH_EVENTS.LOGOUT)
  },

  register: (method = 'email') => {
    telemetry.track(AUTH_EVENTS.REGISTER, { method })
  },

  passwordReset: () => {
    telemetry.track(AUTH_EVENTS.PASSWORD_RESET)
  },
}
