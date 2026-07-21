/**
 * Evidence/Screenshot Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks evidence/screenshot events only.
 */

import { telemetry } from '@/services/telemetry'
import { EVIDENCE_EVENTS } from '@/constants/telemetryEvents'

export const trackEvidence = {
  screenshotModeChange: (oldMode, newMode, templateId = null) => {
    telemetry.track(EVIDENCE_EVENTS.SCREENSHOT_MODE_CHANGE, {
      old_mode: oldMode,
      new_mode: newMode,
      template_id: templateId,
    })
  },

  screenshotCaptured: (executionId, stepId, screenshotType = 'step') => {
    telemetry.track(EVIDENCE_EVENTS.SCREENSHOT_CAPTURED, {
      execution_id: executionId,
      step_id: stepId,
      screenshot_type: screenshotType,
    })
  },

  screenshotView: (executionId, stepId) => {
    telemetry.track(EVIDENCE_EVENTS.SCREENSHOT_VIEW, {
      execution_id: executionId,
      step_id: stepId,
    })
  },

  download: (executionId, format = 'zip') => {
    telemetry.track(EVIDENCE_EVENTS.EVIDENCE_DOWNLOAD, {
      execution_id: executionId,
      format,
    })
  },
}
