/**
 * Plugin Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks plugin events only.
 */

import { telemetry } from '@/services/telemetry'
import { PLUGIN_EVENTS } from '@/constants/telemetryEvents'

export const trackPlugin = {
  search: (query, resultsCount) => {
    telemetry.track(PLUGIN_EVENTS.SEARCH, { query, results_count: resultsCount })
  },

  view: (modelId) => {
    telemetry.track(PLUGIN_EVENTS.VIEW, { model_id: modelId })
  },

  install: (modelId) => {
    telemetry.track(PLUGIN_EVENTS.INSTALL, { model_id: modelId })
  },

  uninstall: (modelId) => {
    telemetry.track(PLUGIN_EVENTS.UNINSTALL, { model_id: modelId })
  },
}
