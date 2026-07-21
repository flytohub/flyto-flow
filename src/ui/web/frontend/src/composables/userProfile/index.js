/**
 * User Profile - Split Modules Re-exports
 *
 * S-Grade: Centralized exports for user profile functionality.
 *
 * Split structure:
 * - state.js: State factory (~60 lines)
 * - profileApi.js: Profile CRUD (~105 lines)
 * - avatarHandlers.js: Avatar handling (~90 lines)
 * - accountActions.js: Account operations (~100 lines)
 * - useUserProfileCore.js: Main composable (~65 lines)
 */

// Main composable
export { useUserProfile } from './useUserProfileCore'

// State
export { createProfileState, DELETE_CONFIRM_PHRASE } from './state'

// API
export { loadProfile, saveProfile } from './profileApi'

// Avatar
export { handleFileSelect, handleCropped, removeAvatar } from './avatarHandlers'

// Account
export {
  deleteAccount,
  copyUserId,
  formatDate,
  clearMessages,
  setSuccessMessage
} from './accountActions'
