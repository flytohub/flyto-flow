/**
 * Activation Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks activation/onboarding events only.
 */

import { telemetry } from '@/services/telemetry'
import { ACTIVATION_EVENTS } from '@/constants/telemetryEvents'

export const trackActivation = {
  onboardingStart: () => {
    telemetry.track(ACTIVATION_EVENTS.ONBOARDING_START)
  },

  onboardingStep: (stepName, stepNumber, totalSteps) => {
    telemetry.track(ACTIVATION_EVENTS.ONBOARDING_STEP, {
      step_name: stepName,
      step_number: stepNumber,
      total_steps: totalSteps,
    })
  },

  onboardingComplete: (durationMs) => {
    telemetry.track(ACTIVATION_EVENTS.ONBOARDING_COMPLETE, { duration_ms: durationMs })
  },

  onboardingSkip: (atStep) => {
    telemetry.track(ACTIVATION_EVENTS.ONBOARDING_SKIP, { at_step: atStep })
  },

  featureDiscover: (featureName) => {
    telemetry.track(ACTIVATION_EVENTS.FEATURE_DISCOVER, { feature_name: featureName })
  },

  helpClick: (context, topic = null) => {
    telemetry.track(ACTIVATION_EVENTS.HELP_CLICK, { context, topic })
  },

  docsVisit: (page) => {
    telemetry.track(ACTIVATION_EVENTS.DOCS_VISIT, { page })
  },
}
