/**
 * Execution Control Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks execution control events only.
 */

import { telemetry } from '@/services/telemetry'
import { EXECUTION_EVENTS } from '@/constants/telemetryEvents'

export const trackExecution = {
  pause: (executionId, reason = 'user_request') => {
    telemetry.track(EXECUTION_EVENTS.PAUSE, { execution_id: executionId, reason })
  },

  resume: (executionId) => {
    telemetry.track(EXECUTION_EVENTS.RESUME, { execution_id: executionId })
  },

  step: (executionId) => {
    telemetry.track(EXECUTION_EVENTS.STEP, { execution_id: executionId })
  },

  resumeFromCheckpoint: (executionId, checkpointId, newExecutionId) => {
    telemetry.track(EXECUTION_EVENTS.RESUME_FROM_CHECKPOINT, {
      execution_id: executionId,
      checkpoint_id: checkpointId,
      new_execution_id: newExecutionId,
    })
  },

  checkpointContinue: (executionId, checkpointId) => {
    telemetry.track(EXECUTION_EVENTS.CHECKPOINT_CONTINUE, {
      execution_id: executionId,
      checkpoint_id: checkpointId,
    })
  },

  checkpointBypass: (executionId, checkpointId, scope) => {
    telemetry.track(EXECUTION_EVENTS.CHECKPOINT_BYPASS, {
      execution_id: executionId,
      checkpoint_id: checkpointId,
      scope,
    })
  },
}
