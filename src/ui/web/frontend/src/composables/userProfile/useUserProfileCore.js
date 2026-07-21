/**
 * User Profile Core
 *
 * S-Grade: Main user profile composable using extracted modules.
 * Handles user profile CRUD operations and avatar management.
 */

import { createProfileState, DELETE_CONFIRM_PHRASE } from './state'
import { loadProfile as loadProfileApi, saveProfile as saveProfileApi } from './profileApi'
import { handleFileSelect as handleFileSelectFn, handleCropped as handleCroppedFn, removeAvatar as removeAvatarFn } from './avatarHandlers'
import { deleteAccount as deleteAccountFn, copyUserId as copyUserIdFn, formatDate, clearMessages as clearMessagesFn, setSuccessMessage as setSuccessMessageFn } from './accountActions'

/**
 * Create user profile composable
 * @param {Object} options
 * @param {Function} options.onSuccess - Success callback
 * @param {Function} options.onError - Error callback
 * @param {Function} options.onLogout - Logout redirect callback
 * @returns {Object} Profile state and methods
 */
export function useUserProfile(options = {}) {
  const { onSuccess, onError, onLogout } = options

  // Create state
  const state = createProfileState()

  // Bound methods
  const loadProfile = () => loadProfileApi(state)
  const saveProfile = () => saveProfileApi(state, { onSuccess, onError })
  const handleFileSelect = (file, maxSizeMB) => handleFileSelectFn(state, file, maxSizeMB, onError)
  const handleCropped = (dataUrl) => handleCroppedFn(state, dataUrl, onError)
  const removeAvatar = () => removeAvatarFn(state)
  const deleteAccount = () => deleteAccountFn(state, { onLogout, onError })
  const copyUserId = () => copyUserIdFn(state)
  const clearMessages = () => clearMessagesFn(state)
  const setSuccessMessage = (msg, duration) => setSuccessMessageFn(state, msg, duration)

  return {
    // State
    loading: state.loading,
    saving: state.saving,
    deleting: state.deleting,
    uploadingAvatar: state.uploadingAvatar,
    errorMessage: state.errorMessage,
    successMessage: state.successMessage,
    currentUser: state.currentUser,
    form: state.form,
    // Avatar state
    showCropper: state.showCropper,
    cropperImageSrc: state.cropperImageSrc,
    // Delete account state
    showDeleteConfirm: state.showDeleteConfirm,
    deleteConfirmText: state.deleteConfirmText,
    deleteConfirmPhrase: DELETE_CONFIRM_PHRASE,
    // Methods
    loadProfile,
    saveProfile,
    copyUserId,
    formatDate,
    handleFileSelect,
    handleCropped,
    removeAvatar,
    deleteAccount,
    clearMessages,
    setSuccessMessage
  }
}
