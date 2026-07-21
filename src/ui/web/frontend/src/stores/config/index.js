/**
 * Config Store Module
 *
 * S-Grade: Re-export all config store functionality.
 *
 * Split modules:
 * - defaults.js: Default configuration values
 * - getters.js: Computed getters
 * - actions.js: Store actions
 * - configStoreCore.js: Main store
 */

// Main store
export { useConfigStore } from './configStoreCore'

// Defaults (for external use if needed)
export { DEFAULTS } from './defaults'

// Getters factory (for testing/composition)
export { createConfigGetters } from './getters'

// Actions factory (for testing/composition)
export { createConfigActions } from './actions'
