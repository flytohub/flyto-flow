/**
 * App Lifecycle Telemetry Tracker (Desktop only)
 *
 * Tracks app launch with version info and update events.
 * Enables version distribution analysis in admin telemetry dashboard.
 */

import { telemetry } from '@/services/telemetry'
import { APP_EVENTS } from '@/constants/telemetryEvents'

export const trackApp = {
  launch: (appVersion, coreVersion) => {
    telemetry.track(APP_EVENTS.LAUNCH, {
      app_version: appVersion || null,
      core_version: coreVersion || null,
      platform: navigator.platform,
    })
  },
}
