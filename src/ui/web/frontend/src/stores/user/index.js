/**
 * User Store - Split Modules Re-exports
 *
 * S-Grade: Centralized exports for user functionality.
 *
 * Split structure:
 * - authHelpers.js: Error mapping utilities (~75 lines)
 * - authActions.js: Auth operations (~160 lines)
 * - userStoreCore.js: Main store (~80 lines)
 */

// Main store
export { useUserStore } from './userStoreCore'

// Helpers for advanced use
export {
  mapLoginError,
  mapRegisterError,
  mapPasswordError,
  createAuthWaiter
} from './authHelpers'

export { createAuthActions } from './authActions'
