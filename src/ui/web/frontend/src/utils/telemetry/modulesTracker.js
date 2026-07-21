/**
 * Modules Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks module catalog events only.
 */

import { telemetry } from '@/services/telemetry'
import { MODULE_EVENTS } from '@/constants/telemetryEvents'

export const trackModules = {
  catalogLoad: (totalCount, defaultCount, expertCount, categoriesCount) => {
    telemetry.track(MODULE_EVENTS.CATALOG_LOAD, {
      total_modules: totalCount,
      default_count: defaultCount,
      expert_count: expertCount,
      categories_count: categoriesCount,
    })
  },

  search: (query, resultsCount) => {
    telemetry.track(MODULE_EVENTS.SEARCH, { query, results_count: resultsCount })
  },

  viewDetails: (moduleId) => {
    telemetry.track(MODULE_EVENTS.VIEW_DETAILS, { module_id: moduleId })
  },

  select: (moduleId, category, source = 'catalog') => {
    telemetry.track(MODULE_EVENTS.SELECT, {
      module_id: moduleId,
      category,
      source,
    })
  },
}
