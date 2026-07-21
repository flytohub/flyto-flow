/**
 * Plugin Store
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All plugin logic split into plugin/* directory.
 *
 * Split modules:
 * - plugin/state.js: State refs and getters
 * - plugin/searchActions.js: Search and model info actions
 * - plugin/installActions.js: Install/uninstall actions
 * - plugin/utilityActions.js: Status, cache, utility actions
 * - plugin/pluginStoreCore.js: Main store
 */

// Re-export all from split modules
export {
  usePluginStore,
  createPluginState,
  createPluginGetters,
  createSearchActions,
  createInstallActions,
  createUtilityActions
} from './plugin/index'
