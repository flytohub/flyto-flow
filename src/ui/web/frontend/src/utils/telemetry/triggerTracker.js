/**
 * Trigger Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks trigger events only.
 */

import { telemetry } from '@/services/telemetry'
import { TRIGGER_EVENTS } from '@/constants/telemetryEvents'

export const trackTrigger = {
  scheduleCreate: (templateId, cronExpression) => {
    telemetry.track(TRIGGER_EVENTS.SCHEDULE_CREATE, {
      template_id: templateId,
      cron_expression: cronExpression,
    })
  },

  scheduleUpdate: (scheduleId, changes) => {
    telemetry.track(TRIGGER_EVENTS.SCHEDULE_UPDATE, {
      schedule_id: scheduleId,
      ...changes,
    })
  },

  scheduleDelete: (scheduleId) => {
    telemetry.track(TRIGGER_EVENTS.SCHEDULE_DELETE, { schedule_id: scheduleId })
  },

  scheduleToggle: (scheduleId, enabled) => {
    telemetry.track(TRIGGER_EVENTS.SCHEDULE_TOGGLE, { schedule_id: scheduleId, enabled })
  },

  schedulePause: (scheduleId, workflowId = null) => {
    telemetry.track(TRIGGER_EVENTS.SCHEDULE_TOGGLE, {
      schedule_id: scheduleId,
      enabled: false,
      action: 'pause',
      workflow_id: workflowId,
    })
  },

  scheduleResume: (scheduleId, workflowId = null) => {
    telemetry.track(TRIGGER_EVENTS.SCHEDULE_TOGGLE, {
      schedule_id: scheduleId,
      enabled: true,
      action: 'resume',
      workflow_id: workflowId,
    })
  },

  scheduleManualTrigger: (scheduleId, workflowId = null) => {
    telemetry.track('trigger.schedule_manual', {
      schedule_id: scheduleId,
      workflow_id: workflowId,
    })
  },

  webhookCreate: (templateId) => {
    telemetry.track(TRIGGER_EVENTS.WEBHOOK_CREATE, { template_id: templateId })
  },

  webhookDelete: (webhookId) => {
    telemetry.track(TRIGGER_EVENTS.WEBHOOK_DELETE, { webhook_id: webhookId })
  },

  webhookToggle: (webhookId, enabled, workflowId = null) => {
    telemetry.track('trigger.webhook_toggle', {
      webhook_id: webhookId,
      enabled,
      workflow_id: workflowId,
    })
  },

  webhookRegenerate: (webhookId) => {
    telemetry.track(TRIGGER_EVENTS.WEBHOOK_REGENERATE, { webhook_id: webhookId })
  },
}
