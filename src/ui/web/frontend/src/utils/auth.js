/**
 * Auth Utilities
 * Centralized authentication helper functions
 */

import { authAPI } from '@/api/auth'
import i18n from '@/i18n'

/**
 * Get current authenticated user ID
 * @returns {string} User ID
 * @throws {Error} If not authenticated
 */
export function getCurrentUserId() {
  const user = authAPI.getLocalUser()
  if (!user) throw new Error(i18n.global.t('error.notAuthenticated'))
  return user.id || user.uid
}

/**
 * Get current authenticated user info
 * @returns {Object} User object with uid, email, displayName
 * @throws {Error} If not authenticated
 */
export function getCurrentUser() {
  const user = authAPI.getLocalUser()
  if (!user) throw new Error(i18n.global.t('error.notAuthenticated'))
  return {
    uid: user.id || user.uid,
    email: user.email,
    displayName: user.displayName || user.display_name || user.username || user.email?.split('@')[0]
  }
}

/**
 * Wait for auth to be ready and return user ID
 * @returns {Promise<string>} User ID when authenticated
 * @throws {Error} If not authenticated after waiting
 */
export async function waitForAuthAndGetUserId() {
  const user = await authAPI.waitForAuth()
  if (!user) throw new Error(i18n.global.t('error.notAuthenticated'))
  return user.id || user.uid
}
