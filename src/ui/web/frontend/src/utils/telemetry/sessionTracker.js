/**
 * Session Quality Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks session quality events only.
 */

import { telemetry } from '@/services/telemetry'
import { SESSION_EVENTS } from '@/constants/telemetryEvents'

export const trackSession = {
  quality: (sessionId, metrics) => {
    telemetry.track(SESSION_EVENTS.SESSION_QUALITY, {
      session_id: sessionId,
      template_id: metrics?.templateId,
      edit_count: metrics?.editCount || 0,
      test_runs: metrics?.testRuns || 0,
      node_count: metrics?.nodeCount || 0,
      duration_ms: metrics?.durationMs || 0,
      quality_score: metrics?.qualityScore,
    })
  },

  idle: (sessionId, idleDurationMs, lastAction = null) => {
    telemetry.track(SESSION_EVENTS.SESSION_IDLE, {
      session_id: sessionId,
      idle_duration_ms: idleDurationMs,
      last_action: lastAction,
    })
  },

  productive: (sessionId, productiveActions, durationMs) => {
    telemetry.track(SESSION_EVENTS.SESSION_PRODUCTIVE, {
      session_id: sessionId,
      productive_actions: productiveActions,
      duration_ms: durationMs,
    })
  },

  errorRecovery: (originalError, recoveryAction, success, attempts = 1) => {
    telemetry.track(SESSION_EVENTS.ERROR_RECOVERY, {
      original_error: originalError,
      recovery_action: recoveryAction,
      success,
      attempts,
    })
  },

  errorAbandon: (error, lastAction, sessionDurationMs) => {
    telemetry.track(SESSION_EVENTS.ERROR_ABANDON, {
      error,
      last_action: lastAction,
      session_duration_ms: sessionDurationMs,
    })
  },
}
