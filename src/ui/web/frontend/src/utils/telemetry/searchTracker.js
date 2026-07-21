/**
 * Search Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks search events only.
 */

import { telemetry } from '@/services/telemetry'
import { SEARCH_EVENTS } from '@/constants/telemetryEvents'

export const trackSearch = {
  query: (query, context, resultsCount) => {
    telemetry.track(SEARCH_EVENTS.QUERY, {
      query,
      context,
      results_count: resultsCount,
    })
  },

  resultClick: (query, resultIndex, resultType) => {
    telemetry.track(SEARCH_EVENTS.RESULT_CLICK, {
      query,
      result_index: resultIndex,
      result_type: resultType,
    })
  },

  noResults: (query, context) => {
    telemetry.track(SEARCH_EVENTS.NO_RESULTS, { query, context })
  },
}
