/**
 * Template Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks template events only.
 */

import { telemetry } from '@/services/telemetry'
import { TEMPLATE_EVENTS, ACTIVATION_EVENTS } from '@/constants/telemetryEvents'
import { hasMilestone, saveMilestone } from './state'

export const trackTemplate = {
  create: (templateId, props = {}) => {
    telemetry.track(TEMPLATE_EVENTS.CREATE, { template_id: templateId, ...props })

    // Check for first template milestone
    if (!hasMilestone('first_template')) {
      saveMilestone('first_template')
      telemetry.track(ACTIVATION_EVENTS.FIRST_TEMPLATE_CREATE, { template_id: templateId })
    }
  },

  save: (templateId, props = {}) => {
    telemetry.track(TEMPLATE_EVENTS.SAVE, { template_id: templateId, ...props })
  },

  delete: (templateId) => {
    telemetry.track(TEMPLATE_EVENTS.DELETE, { template_id: templateId })
  },

  publish: (templateId, props = {}) => {
    telemetry.track(TEMPLATE_EVENTS.PUBLISH, { template_id: templateId, ...props })

    // Check for first publish milestone
    if (!hasMilestone('first_publish')) {
      saveMilestone('first_publish')
      telemetry.track(ACTIVATION_EVENTS.FIRST_TEMPLATE_PUBLISH, { template_id: templateId })
    }
  },

  unpublish: (templateId) => {
    telemetry.track(TEMPLATE_EVENTS.UNPUBLISH, { template_id: templateId })
  },

  duplicate: (templateId, newTemplateId) => {
    telemetry.track(TEMPLATE_EVENTS.DUPLICATE, {
      source_template_id: templateId,
      new_template_id: newTemplateId,
    })
  },

  import: (source, props = {}) => {
    telemetry.track(TEMPLATE_EVENTS.IMPORT, { source, ...props })
  },

  export: (templateId, format) => {
    telemetry.track(TEMPLATE_EVENTS.EXPORT, { template_id: templateId, format })
  },
}
