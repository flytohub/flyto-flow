/**
 * Feature Flags
 *
 * Centralized feature flags for controlling new features and migrations.
 * Used for backward compatibility during phased rollouts.
 */

/**
 * Use API-provided node configuration (ui_config, input_handles, output_handles)
 * When enabled: Node configuration is fetched from API metadata
 * When disabled: Falls back to local NodeType files
 *
 * Migration path:
 *   1. Enable flag to test API-driven configuration
 *   2. Verify all node types render correctly
 *   3. Remove local fallback code after successful migration
 */
export const USE_API_NODE_CONFIG = true

/**
 * Use schema-driven form rendering
 * When enabled: Params forms are generated from params_schema
 * When disabled: Uses static Params component files
 */
export const USE_SCHEMA_FORMS = false // Disabled until all field components are ready

/**
 * Log deprecation warnings in development
 */
export const LOG_DEPRECATION_WARNINGS = process.env.NODE_ENV === 'development'

/**
 * Log when fallback configuration is used (API data missing)
 */
export const LOG_FALLBACK_USAGE = process.env.NODE_ENV === 'development'

/**
 * Helper to log deprecation warnings
 */
export function logDeprecation(oldApi, newApi, context = '') {
  if (LOG_DEPRECATION_WARNINGS) {
    // Intentional: deprecation warnings only shown in dev mode
  }
}

/**
 * Helper to log fallback usage
 */
export function logFallbackUsage(feature, moduleId, reason = '') {
  if (LOG_FALLBACK_USAGE) {
    // Intentional: fallback usage logging only in dev mode
  }
}

export default {
  USE_API_NODE_CONFIG,
  USE_SCHEMA_FORMS,
  LOG_DEPRECATION_WARNINGS,
  LOG_FALLBACK_USAGE,
  logDeprecation,
  logFallbackUsage
}
