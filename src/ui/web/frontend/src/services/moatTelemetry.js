/**
 * Moat Feature Telemetry
 *
 * Tracks usage of moat (competitive advantage) features:
 * - Evolution (AI suggestions)
 * - Checkpoint (failure recovery)
 * - Data Pinning (output caching)
 * - Collaboration (real-time collaboration)
 *
 * Data is automatically sent to Firebase for analysis by Cloud Functions
 */

import { telemetry } from './telemetry'

// =============================================================================
// Event Names (for analytics grouping)
// =============================================================================

const EVENTS = {
  // Checkpoint related
  CHECKPOINT_FAILURE_SHOW: 'moat.checkpoint.failure_show',
  CHECKPOINT_QUICK_RESUME: 'moat.checkpoint.quick_resume',
  CHECKPOINT_MANUAL_SELECT: 'moat.checkpoint.manual_select',
  CHECKPOINT_RETRY_FROM_START: 'moat.checkpoint.retry_from_start',
  CHECKPOINT_ABANDON: 'moat.checkpoint.abandon',
  CHECKPOINT_TIME_SAVED: 'moat.checkpoint.time_saved',

  // Data Pinning related
  PIN_NODE_OUTPUT: 'moat.pinning.pin_output',
  UNPIN_NODE_OUTPUT: 'moat.pinning.unpin_output',
  PIN_AUTO_ENABLED: 'moat.pinning.auto_enabled',
  PIN_AUTO_DISABLED: 'moat.pinning.auto_disabled',
  PIN_SKIP_EXECUTION: 'moat.pinning.skip_execution',

  // Collaboration related
  COLLAB_SESSION_JOIN: 'moat.collaboration.session_join',
  COLLAB_SESSION_LEAVE: 'moat.collaboration.session_leave',
  COLLAB_RECONNECT: 'moat.collaboration.reconnect',
  COLLAB_CONFLICT_RESOLVED: 'moat.collaboration.conflict_resolved',
  COLLAB_CURSOR_SHARE: 'moat.collaboration.cursor_share',

  // User satisfaction (indirect metrics)
  FEATURE_FRICTION: 'moat.friction',  // Where users get stuck
  FEATURE_SUCCESS: 'moat.success',    // Successfully completed operations
  FEATURE_ERROR: 'moat.error'         // Feature errors
}

// =============================================================================
// Moat Telemetry Object
// =============================================================================

export const moatTelemetry = {
  // ---------------------------------------------------------------------------
  // Checkpoint Tracking
  // ---------------------------------------------------------------------------

  /**
   * Failure recovery panel shown
   */
  trackFailureShow(workflowId, failureNode, checkpointsCount, hasRecommended) {
    return telemetry.track(EVENTS.CHECKPOINT_FAILURE_SHOW, {
      workflow_id: workflowId,
      failure_node: failureNode,
      checkpoints_count: checkpointsCount,
      has_recommended: hasRecommended,
      feature: 'checkpoint'
    })
  },

  /**
   * User used quick resume
   */
  trackQuickResume(workflowId, checkpointId, stepsSkipped) {
    return telemetry.track(EVENTS.CHECKPOINT_QUICK_RESUME, {
      workflow_id: workflowId,
      checkpoint_id: checkpointId,
      steps_skipped: stepsSkipped,
      feature: 'checkpoint'
    })
  },

  /**
   * User manually selected a checkpoint
   */
  trackManualCheckpointSelect(workflowId, checkpointId, wasRecommended) {
    return telemetry.track(EVENTS.CHECKPOINT_MANUAL_SELECT, {
      workflow_id: workflowId,
      checkpoint_id: checkpointId,
      was_recommended: wasRecommended,
      feature: 'checkpoint'
    })
  },

  /**
   * User chose to retry from start
   */
  trackRetryFromStart(workflowId, checkpointsAvailable) {
    return telemetry.track(EVENTS.CHECKPOINT_RETRY_FROM_START, {
      workflow_id: workflowId,
      checkpoints_available: checkpointsAvailable,
      feature: 'checkpoint'
    })
  },

  /**
   * User abandoned recovery
   */
  trackCheckpointAbandon(workflowId, reason) {
    return telemetry.track(EVENTS.CHECKPOINT_ABANDON, {
      workflow_id: workflowId,
      reason,
      feature: 'checkpoint'
    })
  },

  /**
   * Record time saved
   */
  trackTimeSaved(workflowId, savedMs, stepsSkipped) {
    return telemetry.track(EVENTS.CHECKPOINT_TIME_SAVED, {
      workflow_id: workflowId,
      time_saved_ms: savedMs,
      steps_skipped: stepsSkipped,
      feature: 'checkpoint'
    })
  },

  // ---------------------------------------------------------------------------
  // Data Pinning Tracking
  // ---------------------------------------------------------------------------

  /**
   * User pinned node output
   */
  trackPinOutput(workflowId, nodeId, isAutoPin) {
    return telemetry.track(EVENTS.PIN_NODE_OUTPUT, {
      workflow_id: workflowId,
      node_id: nodeId,
      is_auto_pin: isAutoPin,
      feature: 'pinning'
    })
  },

  /**
   * User unpinned output
   */
  trackUnpinOutput(workflowId, nodeId) {
    return telemetry.track(EVENTS.UNPIN_NODE_OUTPUT, {
      workflow_id: workflowId,
      node_id: nodeId,
      feature: 'pinning'
    })
  },

  /**
   * Auto-pin setting changed
   */
  trackAutoPinToggle(enabled) {
    return telemetry.track(enabled ? EVENTS.PIN_AUTO_ENABLED : EVENTS.PIN_AUTO_DISABLED, {
      feature: 'pinning'
    })
  },

  /**
   * Skipped execution of pinned nodes
   */
  trackPinSkipExecution(workflowId, skippedNodes) {
    return telemetry.track(EVENTS.PIN_SKIP_EXECUTION, {
      workflow_id: workflowId,
      skipped_count: skippedNodes?.length || 0,
      feature: 'pinning'
    })
  },

  // ---------------------------------------------------------------------------
  // Collaboration Tracking
  // ---------------------------------------------------------------------------

  /**
   * Join collaboration session
   */
  trackCollabJoin(workflowId, sessionId, participantsCount) {
    return telemetry.track(EVENTS.COLLAB_SESSION_JOIN, {
      workflow_id: workflowId,
      session_id: sessionId,
      participants_count: participantsCount,
      feature: 'collaboration'
    })
  },

  /**
   * Leave collaboration session
   */
  trackCollabLeave(workflowId, sessionId, durationMs) {
    return telemetry.track(EVENTS.COLLAB_SESSION_LEAVE, {
      workflow_id: workflowId,
      session_id: sessionId,
      duration_ms: durationMs,
      feature: 'collaboration'
    })
  },

  /**
   * Reconnect attempt
   */
  trackCollabReconnect(workflowId, attempt, success) {
    return telemetry.track(EVENTS.COLLAB_RECONNECT, {
      workflow_id: workflowId,
      attempt,
      success,
      feature: 'collaboration'
    })
  },

  /**
   * Conflict resolved
   */
  trackConflictResolved(workflowId, conflictType) {
    return telemetry.track(EVENTS.COLLAB_CONFLICT_RESOLVED, {
      workflow_id: workflowId,
      conflict_type: conflictType,
      feature: 'collaboration'
    })
  },

  // ---------------------------------------------------------------------------
  // Friction and Success Tracking (most important analytics metrics)
  // ---------------------------------------------------------------------------

  /**
   * Track where users get stuck (friction points)
   * @param {string} feature - Which feature
   * @param {string} action - What action
   * @param {string} reason - Why they got stuck
   * @param {Object} context - Additional context
   */
  trackFriction(feature, action, reason, context = {}) {
    return telemetry.track(EVENTS.FEATURE_FRICTION, {
      feature,
      action,
      friction_reason: reason,
      ...context
    })
  },

  /**
   * Track successfully completed operations
   * @param {string} feature - Which feature
   * @param {string} action - What action
   * @param {number} durationMs - How long it took
   * @param {Object} context - Additional context
   */
  trackSuccess(feature, action, durationMs = null, context = {}) {
    return telemetry.track(EVENTS.FEATURE_SUCCESS, {
      feature,
      action,
      duration_ms: durationMs,
      ...context
    })
  },

  /**
   * Track feature errors
   * @param {string} feature - Which feature
   * @param {string} action - What action
   * @param {string} error - Error message
   * @param {Object} context - Additional context
   */
  trackError(feature, action, error, context = {}) {
    return telemetry.track(EVENTS.FEATURE_ERROR, {
      feature,
      action,
      error_message: error,
      ...context
    })
  }
}

// =============================================================================
// Timer utility (for tracking operation duration)
// =============================================================================

const timers = new Map()

export const moatTimer = {
  /**
   * Start timer
   * @param {string} key - Timer key
   */
  start(key) {
    timers.set(key, Date.now())
  },

  /**
   * End timer and return duration
   * @param {string} key - Timer key
   * @returns {number|null} Duration in milliseconds
   */
  end(key) {
    const start = timers.get(key)
    if (start) {
      timers.delete(key)
      return Date.now() - start
    }
    return null
  },

  /**
   * Clear timer
   * @param {string} key - Timer key
   */
  clear(key) {
    timers.delete(key)
  }
}

// =============================================================================
// Export
// =============================================================================

export default moatTelemetry
