/**
 * User Profile State
 *
 * S-Grade: State factory for user profile composable.
 * Single responsibility: Create reactive state.
 */

import { ref, reactive } from 'vue'

/** Confirmation phrase for account deletion */
export const DELETE_CONFIRM_PHRASE = 'DELETE MY ACCOUNT'

/**
 * Create user profile state
 * @returns {Object} Reactive state objects
 */
export function createProfileState() {
  // Loading states
  const loading = ref(true)
  const saving = ref(false)
  const deleting = ref(false)
  const uploadingAvatar = ref(false)

  // Messages
  const errorMessage = ref('')
  const successMessage = ref('')

  // User data
  const currentUser = ref(null)

  // Form state - all fields in camelCase
  const form = reactive({
    displayName: '',
    username: '',
    bio: '',
    avatarUrl: ''
  })

  // Avatar state
  const showCropper = ref(false)
  const cropperImageSrc = ref('')
  const oldAvatarUrl = ref('')

  // Delete account state
  const showDeleteConfirm = ref(false)
  const deleteConfirmText = ref('')

  return {
    loading,
    saving,
    deleting,
    uploadingAvatar,
    errorMessage,
    successMessage,
    currentUser,
    form,
    showCropper,
    cropperImageSrc,
    oldAvatarUrl,
    showDeleteConfirm,
    deleteConfirmText
  }
}
