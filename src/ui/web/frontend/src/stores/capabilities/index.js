/**
 * Capabilities Store - Split Modules Re-exports
 *
 * S-Grade: Centralized exports for capabilities functionality.
 *
 * Split structure:
 * - pageAccessHelpers.js: Route access control (~70 lines)
 * - featureFlagHelpers.js: Capability check utilities (~75 lines)
 * - capabilitiesStoreCore.js: Main store (~190 lines)
 */

// Main store
export { useCapabilitiesStore } from './capabilitiesStoreCore'

// Helpers
export {
  ALWAYS_ALLOWED_PAGES,
  isAlwaysAllowed,
  checkPageAccess,
  createPageAccessChecker
} from './pageAccessHelpers'

export {
  createCapabilityCheckers,
  DEFAULT_CAPABILITIES,
  DEFAULT_FEATURES,
  DEFAULT_UI
} from './featureFlagHelpers'
