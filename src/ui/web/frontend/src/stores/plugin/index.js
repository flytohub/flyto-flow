/**
 * Plugin Store Module
 *
 * S-Grade: Re-export all plugin store functionality.
 *
 * Split modules:
 * - state.js: State refs and getters
 * - searchActions.js: Search and model info actions
 * - installActions.js: Install/uninstall actions
 * - utilityActions.js: Status, cache, utility actions
 * - pluginStoreCore.js: Main store
 */

// Main store
export { usePluginStore } from './pluginStoreCore'

// State factory (for testing/composition)
export { createPluginState, createPluginGetters } from './state'

// Action factories (for testing/composition)
export { createSearchActions } from './searchActions'
export { createInstallActions } from './installActions'
export { createUtilityActions } from './utilityActions'
