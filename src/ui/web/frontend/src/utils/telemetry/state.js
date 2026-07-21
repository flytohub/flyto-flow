/**
 * Telemetry State Module
 *
 * S-Grade: Single responsibility - manages telemetry session state only.
 * Shared state for milestone tracking across all telemetry modules.
 */

// Session tracking state
export const sessionState = {
  builderSessionStart: null,
  currentTemplateId: null,
  activationMilestones: new Set(),
}

// Load milestones from localStorage
try {
  const stored = localStorage.getItem('telemetry_milestones')
  if (stored) {
    sessionState.activationMilestones = new Set(JSON.parse(stored))
  }
} catch (e) {
  // Ignore localStorage errors
}

/**
 * Save milestone to localStorage
 */
export function saveMilestone(milestone) {
  sessionState.activationMilestones.add(milestone)
  try {
    localStorage.setItem(
      'telemetry_milestones',
      JSON.stringify([...sessionState.activationMilestones])
    )
  } catch (e) {
    // Ignore localStorage errors
  }
}

/**
 * Check if milestone already achieved
 */
export function hasMilestone(milestone) {
  return sessionState.activationMilestones.has(milestone)
}
