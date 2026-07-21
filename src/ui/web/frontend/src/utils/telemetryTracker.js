/**
 * Telemetry Tracker Utility
 *
 * S-Grade: This file is being deprecated in favor of split modules.
 * New code should import from '@/utils/telemetry' instead.
 *
 * Split modules:
 * - authTracker - Authentication events
 * - templateTracker - Template CRUD events
 * - workflowTracker - Workflow execution events
 * - executionTracker - Execution control events
 * - builderTracker - Builder session events
 * - marketplaceTracker - Marketplace events
 * - aiTracker - AI assistant events
 * - pluginTracker - Plugin events
 * - organizationTracker - Organization events
 * - uxTracker - UX friction events
 * - activationTracker - Activation/onboarding events
 * - settingsTracker - Settings events
 * - searchTracker - Search events
 * - dashboardTracker - Dashboard events
 * - modulesTracker - Module catalog events
 * - variableTracker - Variable/credential events
 * - triggerTracker - Trigger events
 * - alertTracker - Alert events
 * - trialTracker - Trial mode events
 * - evidenceTracker - Evidence/screenshot events
 * - segmentTracker - Segment/classification events
 * - performanceTracker - Performance events
 * - sessionTracker - Session quality events
 */

// Re-export everything from split modules
export {
  trackAuth,
  trackTemplate,
  trackWorkflow,
  trackExecution,
  trackBuilder,
  trackMarketplace,
  trackAI,
  trackPlugin,
  trackOrganization,
  trackUX,
  trackActivation,
  trackSettings,
  trackSearch,
  trackDashboard,
  trackModules,
  trackVariable,
  trackCredential,
  trackTrigger,
  trackAlert,
  trackTrial,
  trackEvidence,
  trackSegment,
  trackPerformance,
  trackSession,
} from './telemetry'

// Default export for backwards compatibility
export { default } from './telemetry'
