/**
 * User Profile Composable
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All functionality split into composables/userProfile/* directory.
 *
 * Split modules:
 * - userProfile/state.js: State factory
 * - userProfile/profileApi.js: Profile CRUD
 * - userProfile/avatarHandlers.js: Avatar handling
 * - userProfile/accountActions.js: Account operations
 * - userProfile/useUserProfileCore.js: Main composable
 */

// Re-export main composable
export { useUserProfile } from './userProfile'

// Re-export utilities for advanced use
export {
  createProfileState,
  DELETE_CONFIRM_PHRASE,
  formatDate,
  copyUserId,
  clearMessages,
  setSuccessMessage
} from './userProfile'
