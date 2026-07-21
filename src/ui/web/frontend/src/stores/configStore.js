/**
 * Config Store
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All config logic split into config/* directory.
 *
 * Split modules:
 * - config/defaults.js: Default configuration values
 * - config/getters.js: Computed getters
 * - config/actions.js: Store actions
 * - config/configStoreCore.js: Main store
 */

// Re-export all from split modules
export {
  useConfigStore,
  DEFAULTS,
  createConfigGetters,
  createConfigActions
} from './config/index'
