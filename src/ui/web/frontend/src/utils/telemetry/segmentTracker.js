/**
 * Segment/User Classification Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks segment/classification events only.
 */

import { telemetry } from '@/services/telemetry'
import { SEGMENT_EVENTS } from '@/constants/telemetryEvents'

export const trackSegment = {
  identifyUser: (userId, segment, plan = null) => {
    telemetry.track(SEGMENT_EVENTS.USER_SEGMENT_IDENTIFIED, {
      user_id: userId,
      segment, // free, trial, paid, enterprise
      plan,
    })
  },

  classifyUserType: (userId, userType) => {
    telemetry.track(SEGMENT_EVENTS.USER_TYPE_CLASSIFIED, {
      user_id: userId,
      user_type: userType, // creator, executor, analyst, viewer
    })
  },

  skillLevel: (userId, level, indicators = {}) => {
    telemetry.track(SEGMENT_EVENTS.USER_SKILL_LEVEL, {
      user_id: userId,
      skill_level: level, // novice, intermediate, advanced
      ...indicators,
    })
  },

  usageIntensity: (userId, intensity, metrics) => {
    telemetry.track(SEGMENT_EVENTS.USAGE_INTENSITY, {
      user_id: userId,
      intensity, // low, medium, high
      execute_count: metrics?.executeCount,
      builder_sessions: metrics?.builderSessions,
      period: metrics?.period || '7d',
    })
  },

  signupCohort: (userId, signupDate, signupSource = null) => {
    telemetry.track(SEGMENT_EVENTS.SIGNUP_COHORT, {
      user_id: userId,
      signup_date: signupDate,
      signup_source: signupSource,
    })
  },

  activationCohort: (userId, firstExecutionDate, daysToActivation) => {
    telemetry.track(SEGMENT_EVENTS.ACTIVATION_COHORT, {
      user_id: userId,
      first_execution_date: firstExecutionDate,
      days_to_activation: daysToActivation,
    })
  },
}
