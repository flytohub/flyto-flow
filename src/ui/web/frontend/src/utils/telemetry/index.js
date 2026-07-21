/**
 * Telemetry Tracker Index
 *
 * S-Grade: Re-exports all split telemetry trackers for backwards compatibility.
 * New code should import specific trackers directly.
 */

// State (for advanced usage)
export { sessionState, saveMilestone, hasMilestone } from './state'

// Individual trackers
export { trackApp } from './appTracker'
export { trackAuth } from './authTracker'
export { trackTemplate } from './templateTracker'
export { trackWorkflow } from './workflowTracker'
export { trackExecution } from './executionTracker'
export { trackBuilder } from './builderTracker'
export { trackMarketplace } from './marketplaceTracker'
export { trackAI } from './aiTracker'
export { trackPlugin } from './pluginTracker'
export { trackOrganization } from './organizationTracker'
export { trackUX } from './uxTracker'
export { trackActivation } from './activationTracker'
export { trackSettings } from './settingsTracker'
export { trackSearch } from './searchTracker'
export { trackDashboard } from './dashboardTracker'
export { trackModules } from './modulesTracker'
export { trackVariable, trackCredential } from './variableTracker'
export { trackTrigger } from './triggerTracker'
export { trackAlert } from './alertTracker'
export { trackTrial } from './trialTracker'
export { trackEvidence } from './evidenceTracker'
export { trackSegment } from './segmentTracker'
export { trackPerformance } from './performanceTracker'
export { trackSession } from './sessionTracker'

// Default export for backwards compatibility
import { trackApp } from './appTracker'
import { trackAuth } from './authTracker'
import { trackTemplate } from './templateTracker'
import { trackWorkflow } from './workflowTracker'
import { trackExecution } from './executionTracker'
import { trackBuilder } from './builderTracker'
import { trackMarketplace } from './marketplaceTracker'
import { trackAI } from './aiTracker'
import { trackPlugin } from './pluginTracker'
import { trackOrganization } from './organizationTracker'
import { trackUX } from './uxTracker'
import { trackActivation } from './activationTracker'
import { trackSettings } from './settingsTracker'
import { trackSearch } from './searchTracker'
import { trackDashboard } from './dashboardTracker'
import { trackModules } from './modulesTracker'
import { trackVariable, trackCredential } from './variableTracker'
import { trackTrigger } from './triggerTracker'
import { trackAlert } from './alertTracker'
import { trackTrial } from './trialTracker'
import { trackEvidence } from './evidenceTracker'
import { trackSegment } from './segmentTracker'
import { trackPerformance } from './performanceTracker'
import { trackSession } from './sessionTracker'

export default {
  app: trackApp,
  auth: trackAuth,
  template: trackTemplate,
  workflow: trackWorkflow,
  execution: trackExecution,
  builder: trackBuilder,
  marketplace: trackMarketplace,
  ai: trackAI,
  plugin: trackPlugin,
  organization: trackOrganization,
  ux: trackUX,
  activation: trackActivation,
  settings: trackSettings,
  search: trackSearch,
  dashboard: trackDashboard,
  modules: trackModules,
  variable: trackVariable,
  credential: trackCredential,
  trigger: trackTrigger,
  alert: trackAlert,
  trial: trackTrial,
  evidence: trackEvidence,
  segment: trackSegment,
  performance: trackPerformance,
  session: trackSession,
}
