/**
 * Auth Helpers
 *
 * S-Grade: Authentication utility functions.
 * Single responsibility: Error mapping and utilities.
 */

import i18n from '@/i18n'

/**
 * Map login error message to user-friendly message
 * @param {string} msg - Error message
 * @returns {string} User-friendly message
 */
export function mapLoginError(msg) {
  if (msg.includes('invalid') || msg.includes('wrong') || msg.includes('not found')) {
    return 'Invalid email or password'
  }
  if (msg.includes('too many')) {
    return 'Too many attempts. Please try again later.'
  }
  return msg || i18n.global.t('error.loginFailed')
}

/**
 * Map registration error message to user-friendly message
 * @param {string} msg - Error message
 * @returns {string} User-friendly message
 */
export function mapRegisterError(msg) {
  if (msg.includes('already') || msg.includes('exists')) {
    return 'Email already in use'
  }
  if (msg.includes('weak') || msg.includes('password')) {
    return 'Password is too weak (minimum 6 characters)'
  }
  if (msg.includes('invalid') && msg.includes('email')) {
    return 'Invalid email format'
  }
  return msg || i18n.global.t('error.registrationFailed')
}

/**
 * Map password change error message
 * @param {string} msg - Error message
 * @returns {string} User-friendly message
 */
export function mapPasswordError(msg) {
  if (msg.includes('incorrect') || msg.includes('wrong')) {
    return 'Current password is incorrect'
  }
  return msg || i18n.global.t('error.passwordChangeFailed')
}

/**
 * Wait for auth to be ready.
 *
 * Resolves when initAuth() has completed — i.e. user.value has been
 * resolved against /auth/me (or set to null on auth failure). The
 * authInitialized flag is flipped in initAuth's finally block, not at
 * the start, so callers can trust userStore.userId after this resolves.
 *
 * The 5s timeout is an escape hatch for genuinely hung backends; it
 * should not normally fire. If it does, callers should re-check
 * userStore.userId rather than assume auth succeeded.
 *
 * @returns {Promise<void>}
 */
export function createAuthWaiter(isLoading, authInitialized) {
  return async function waitForAuth(timeoutMs = 5000) {
    if (!isLoading.value && authInitialized.value) return

    return new Promise((resolve) => {
      const checkInterval = setInterval(() => {
        if (!isLoading.value && authInitialized.value) {
          clearInterval(checkInterval)
          resolve()
        }
      }, 50)

      // Prevent infinite hang — resolve after timeout even if auth never initializes
      setTimeout(() => {
        clearInterval(checkInterval)
        resolve()
      }, timeoutMs)
    })
  }
}
