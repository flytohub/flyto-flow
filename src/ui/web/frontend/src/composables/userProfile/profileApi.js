/**
 * Profile API Actions
 *
 * S-Grade: Profile load and save operations.
 * Single responsibility: Profile CRUD via Gateway API.
 */

import i18n from '@/i18n'
import { authAPI } from '@/api/auth'
import { get, patch } from '@/api/client'
import { ENDPOINTS } from '@/config/api'
import { deleteFile, extractFileIdFromUrl } from '@/api/storage'

/**
 * Load user profile from Gateway API
 * @param {Object} state - Profile state object
 * @returns {Promise<void>}
 */
export async function loadProfile(state) {
  const { loading, currentUser, form, oldAvatarUrl } = state

  loading.value = true
  try {
    currentUser.value = authAPI.getLocalUser()
    const uid = currentUser.value?.uid || currentUser.value?.id

    if (!uid) {
      throw new Error(i18n.global.t('error.notAuthenticated'))
    }

    const result = await get(ENDPOINTS.USERS.PROFILE)
    const profile = result.profile || result

    if (profile) {
      // client.js auto-converts API response to camelCase
      // Use currentUser (from auth/me) as primary source for displayName if profile is empty
      form.displayName = profile.displayName || currentUser.value?.displayName || ''
      form.username = profile.username || ''
      form.bio = profile.bio || ''
      form.avatarUrl = profile.avatarUrl || ''
      oldAvatarUrl.value = form.avatarUrl

      if (profile.createdAt) {
        currentUser.value.createdAt = profile.createdAt
      }
    } else {
      form.displayName = currentUser.value?.displayName || currentUser.value?.email?.split('@')[0] || ''
    }
  } catch (err) {
    if (currentUser.value) {
      form.displayName = currentUser.value.displayName || currentUser.value.email?.split('@')[0] || ''
    }
  } finally {
    loading.value = false
  }
}

/**
 * Save profile via Gateway API
 * @param {Object} state - Profile state object
 * @param {Object} callbacks - Callback functions
 * @returns {Promise<boolean>} Success status
 */
export async function saveProfile(state, callbacks = {}) {
  const { saving, currentUser, form, oldAvatarUrl, errorMessage, successMessage } = state
  const { onSuccess, onError } = callbacks

  if (saving.value) return false

  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const uid = currentUser.value?.uid || currentUser.value?.id
    if (!uid) {
      throw new Error(i18n.global.t('error.notAuthenticated'))
    }

    // Use camelCase - client.js will convert to snake_case for API
    const payload = {
      displayName: form.displayName,
      username: form.username,
      bio: form.bio?.substring(0, 200) || '',
      avatarUrl: form.avatarUrl || ''
    }

    const result = await patch(ENDPOINTS.USERS.PROFILE, payload)

    if (result.ok) {
      // Delete old avatar from storage after successful save
      if (oldAvatarUrl.value && oldAvatarUrl.value !== form.avatarUrl) {
        const oldFileId = extractFileIdFromUrl(oldAvatarUrl.value)
        if (oldFileId) {
          await deleteFile(oldFileId)
        }
      }
      oldAvatarUrl.value = form.avatarUrl

      onSuccess?.('saved')
      return true
    } else {
      throw new Error(result.error || 'Failed to save profile')
    }
  } catch (err) {
    onError?.(err)
    errorMessage.value = err.message
    return false
  } finally {
    saving.value = false
  }
}
