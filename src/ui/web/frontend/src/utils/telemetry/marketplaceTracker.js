/**
 * Marketplace Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks marketplace events only.
 */

import { telemetry } from '@/services/telemetry'
import { MARKETPLACE_EVENTS, ACTIVATION_EVENTS } from '@/constants/telemetryEvents'
import { hasMilestone, saveMilestone } from './state'

export const trackMarketplace = {
  search: (query, resultsCount, filters = {}) => {
    telemetry.track(MARKETPLACE_EVENTS.SEARCH, {
      query,
      results_count: resultsCount,
      ...filters,
    })
  },

  filter: (filterType, filterValue) => {
    telemetry.track(MARKETPLACE_EVENTS.FILTER, {
      filter_type: filterType,
      filter_value: filterValue,
    })
  },

  sort: (sortBy, sortOrder) => {
    telemetry.track(MARKETPLACE_EVENTS.SORT, { sort_by: sortBy, sort_order: sortOrder })
  },

  viewTemplate: (templateId, source = 'browse') => {
    telemetry.track(MARKETPLACE_EVENTS.VIEW_TEMPLATE, {
      template_id: templateId,
      source,
    })
  },

  previewTemplate: (templateId) => {
    telemetry.track(MARKETPLACE_EVENTS.PREVIEW_TEMPLATE, { template_id: templateId })
  },

  install: (templateId, templateName = null, pricing = null, category = null) => {
    telemetry.track(MARKETPLACE_EVENTS.INSTALL, {
      template_id: templateId,
      template_name: templateName,
      pricing,
      category,
    })
  },

  uninstall: (templateId) => {
    telemetry.track(MARKETPLACE_EVENTS.UNINSTALL, { template_id: templateId })
  },

  purchaseStart: (templateId, price, currency = 'usd') => {
    telemetry.track(MARKETPLACE_EVENTS.PURCHASE_START, {
      template_id: templateId,
      price,
      currency,
    })
  },

  purchaseComplete: (templateId, price, currency = 'usd', orderId = null) => {
    telemetry.track(MARKETPLACE_EVENTS.PURCHASE_COMPLETE, {
      template_id: templateId,
      price,
      currency,
      order_id: orderId,
    })

    // Check for first purchase milestone
    if (!hasMilestone('first_purchase')) {
      saveMilestone('first_purchase')
      telemetry.track(ACTIVATION_EVENTS.FIRST_PURCHASE, {
        template_id: templateId,
        price,
      })
    }
  },

  purchaseAbandon: (templateId, step, reason = null) => {
    telemetry.track(MARKETPLACE_EVENTS.PURCHASE_ABANDON, {
      template_id: templateId,
      abandon_step: step,
      reason,
    })
  },

  favoriteAdd: (templateId) => {
    telemetry.track(MARKETPLACE_EVENTS.FAVORITE_ADD, { template_id: templateId })
  },

  favoriteRemove: (templateId) => {
    telemetry.track(MARKETPLACE_EVENTS.FAVORITE_REMOVE, { template_id: templateId })
  },

  share: (templateId, method) => {
    telemetry.track(MARKETPLACE_EVENTS.SHARE, { template_id: templateId, method })
  },
}
