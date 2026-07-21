/**
 * User Store
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All functionality split into stores/user/* directory.
 *
 * Split modules:
 * - user/authHelpers.js: Error mapping utilities
 * - user/authActions.js: Auth operations
 * - user/userStoreCore.js: Main store
 */

// Re-export store
export { useUserStore } from './user'

// Re-export helpers for advanced use
export {
  mapLoginError,
  mapRegisterError,
  mapPasswordError,
  createAuthWaiter,
  createAuthActions
} from './user'
