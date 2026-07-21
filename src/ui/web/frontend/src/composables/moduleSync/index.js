/**
 * Module Sync Composables
 *
 * S-Grade: Re-export all module sync functionality.
 *
 * Split modules:
 * - cacheUtils.js: Module cache operations
 * - versionCheck.js: Version check utilities
 * - websocket.js: WebSocket connection manager
 * - useModuleSyncCore.js: Main composable
 */

// Cache utilities
export {
  clearModuleCache,
  getCachedVersion,
  setCachedVersion,
  MODULE_VERSION_KEY,
  MODULE_CACHE_PREFIX
} from './cacheUtils'

// Version check utilities
export {
  fetchModuleVersion,
  checkForModuleUpdates,
  triggerModuleReload
} from './versionCheck'

// WebSocket manager
export { createWebSocketManager } from './websocket'

// Main composable
export { useModuleSync, onModulesUpdated } from './useModuleSyncCore'
