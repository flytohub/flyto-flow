/**
 * Feature Flag Helpers
 *
 * S-Grade: Feature flag utilities extracted from capabilities store.
 * Single responsibility: capability checking.
 *
 * SECURITY NOTE:
 * The default values below are FALLBACKS for offline/error scenarios only.
 * Authoritative capability configuration comes from the backend:
 * - /api/capabilities - Returns all enabled capabilities
 * - /api/config/defaults - Returns default configuration (planned)
 *
 * These defaults are designed to "fail closed" for security:
 * - Most features default to false (no access)
 * - Only core workflow functionality is enabled by default
 *
 * Never trust these defaults for access control decisions.
 * Always verify against backend-provided values when available.
 */

/**
 * Create capability checker
 * @param {Ref} capabilitiesRef - Reactive capabilities array
 * @returns {Object} Capability check functions
 */
export function createCapabilityCheckers(capabilitiesRef) {
  return {
    /**
     * Check if a specific capability is available
     * @param {string} capability - Capability name
     * @returns {boolean}
     */
    hasCapability(capability) {
      return capabilitiesRef.value.includes(capability)
    },

    /**
     * Check if any of the given capabilities are available
     * @param {...string} caps - Capability names
     * @returns {boolean}
     */
    hasAnyCapability(...caps) {
      return caps.some(cap => capabilitiesRef.value.includes(cap))
    },

    /**
     * Check if all of the given capabilities are available
     * @param {...string} caps - Capability names
     * @returns {boolean}
     */
    hasAllCapabilities(...caps) {
      return caps.every(cap => capabilitiesRef.value.includes(cap))
    }
  }
}

/**
 * Default capabilities for offline fallback
 *
 * SECURITY NOTE: Minimal capabilities for offline mode.
 * Designed to fail closed - only core functionality enabled.
 * Backend /api/capabilities returns authoritative list.
 *
 * @deprecated Prefer using backend-provided capabilities from /api/capabilities
 */
export const DEFAULT_CAPABILITIES = [
  'core.workflow_run',
  'core.template_builder',
  'core.execution_history',
  'core.basic_logging'
]

/**
 * Default features for offline fallback
 *
 * SECURITY NOTE: All advanced features disabled by default.
 * This ensures fail-closed behavior when backend is unavailable.
 * Backend returns authoritative feature flags.
 *
 * @deprecated Prefer using backend-provided features from /api/capabilities
 */
export const DEFAULT_FEATURES = {
  marketplace: false,
  billing: false,
  observability: false,
  versioning: false,
  audit: false,
  selfSignup: false
}

/**
 * Default UI config for offline fallback
 *
 * SECURITY NOTE: UI visibility defaults to hidden for most features.
 * Backend computes actual visibility based on user's license.
 *
 * @deprecated Prefer using backend-provided UI config from /api/capabilities
 */
export const DEFAULT_UI = {
  showMarketplace: false,
  showObservability: false,
  showVersioning: false,
  showAudit: false,
  licenseType: 'free',
  isLicensed: false,
  canUpgrade: true
}
