/**
 * Capabilities Store
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All functionality split into stores/capabilities/* directory.
 *
 * Split modules:
 * - capabilities/pageAccessHelpers.js: Route access control
 * - capabilities/featureFlagHelpers.js: Capability utilities
 * - capabilities/capabilitiesStoreCore.js: Main store
 */

// Re-export store
export { useCapabilitiesStore } from './capabilities'

// Re-export helpers for advanced use
export {
  ALWAYS_ALLOWED_PAGES,
  isAlwaysAllowed,
  checkPageAccess,
  createPageAccessChecker,
  createCapabilityCheckers,
  DEFAULT_CAPABILITIES,
  DEFAULT_FEATURES,
  DEFAULT_UI
} from './capabilities'
