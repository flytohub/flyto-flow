/**
 * Workflow Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks workflow events only.
 */

import { telemetry } from '@/services/telemetry'
import { WORKFLOW_EVENTS, ACTIVATION_EVENTS } from '@/constants/telemetryEvents'
import { hasMilestone, saveMilestone } from './state'

export const trackWorkflow = {
  executeStart: (workflowId, templateId, trigger = 'manual') => {
    telemetry.track(WORKFLOW_EVENTS.EXECUTE_START, {
      workflow_id: workflowId,
      template_id: templateId,
      trigger,
    })

    // Check for first execution milestone
    if (!hasMilestone('first_execute')) {
      saveMilestone('first_execute')
      telemetry.track(ACTIVATION_EVENTS.FIRST_WORKFLOW_EXECUTE, {
        workflow_id: workflowId,
        template_id: templateId,
      })
    }
  },

  executeComplete: (workflowId, durationMs, stepsCount) => {
    telemetry.track(WORKFLOW_EVENTS.EXECUTE_COMPLETE, {
      workflow_id: workflowId,
      duration_ms: durationMs,
      steps_count: stepsCount,
    })
  },

  executeError: (workflowId, error, stepId = null) => {
    telemetry.track(WORKFLOW_EVENTS.EXECUTE_ERROR, {
      workflow_id: workflowId,
      error: typeof error === 'string' ? error : error?.message,
      step_id: stepId,
    })
  },

  executeCancel: (workflowId, reason = null) => {
    telemetry.track(WORKFLOW_EVENTS.EXECUTE_CANCEL, {
      workflow_id: workflowId,
      reason,
    })
  },
}
