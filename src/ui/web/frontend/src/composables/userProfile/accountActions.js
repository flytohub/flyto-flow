/**
 * Account Actions
 *
 * S-Grade: Account management and utility functions.
 * Single responsibility: Account operations.
 */

import i18n from '@/i18n'
import { authAPI } from '@/api/auth'
import { del } from '@/api/client'
import { ENDPOINTS } from '@/config/api'
import { DELETE_CONFIRM_PHRASE } from './state'

/**
 * Delete account via Gateway API
 * @param {Object} state - Profile state object
 * @param {Object} callbacks - Callback functions
 * @returns {Promise<boolean>} Success status
 */
export async function deleteAccount(state, callbacks = {}) {
  const { deleting, currentUser, errorMessage, showDeleteConfirm, deleteConfirmText } = state
  const { onLogout, onError } = callbacks

  if (deleteConfirmText.value !== DELETE_CONFIRM_PHRASE || deleting.value) {
    return false
  }

  deleting.value = true
  errorMessage.value = ''

  try {
    const uid = currentUser.value?.uid || currentUser.value?.id
    if (!uid) {
      throw new Error(i18n.global.t('error.notAuthenticated'))
    }

    const result = await del(ENDPOINTS.USERS.PROFILE)

    if (result.ok) {
      authAPI.logout()
      onLogout?.()
      return true
    } else {
      throw new Error(result.error || 'Failed to delete account')
    }
  } catch (err) {
    if (err.message?.includes('recent')) {
      errorMessage.value = 'Please sign out and sign in again before deleting your account'
    } else {
      errorMessage.value = err.message
    }
    onError?.(err)
    return false
  } finally {
    deleting.value = false
    showDeleteConfirm.value = false
    deleteConfirmText.value = ''
  }
}

/**
 * Copy user ID to clipboard
 * @param {Object} state - Profile state object
 * @returns {boolean} Success status
 */
export function copyUserId(state) {
  const uid = state.currentUser.value?.uid || state.currentUser.value?.id
  if (uid) {
    navigator.clipboard.writeText(uid)
    return true
  }
  return false
}

/**
 * Format date for display
 * @param {string} dateStr - Date string
 * @returns {string} Formatted date
 */
export function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

/**
 * Clear messages
 * @param {Object} state - Profile state object
 */
export function clearMessages(state) {
  state.errorMessage.value = ''
  state.successMessage.value = ''
}

/**
 * Set success message with auto-clear
 * @param {Object} state - Profile state object
 * @param {string} message - Message text
 * @param {number} duration - Duration in ms (0 for permanent)
 */
export function setSuccessMessage(state, message, duration = 3000) {
  state.successMessage.value = message
  if (duration > 0) {
    setTimeout(() => {
      state.successMessage.value = ''
    }, duration)
  }
}
