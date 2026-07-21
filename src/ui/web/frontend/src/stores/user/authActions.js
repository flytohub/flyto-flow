/**
 * Auth Actions
 *
 * S-Grade: Authentication action functions.
 * Single responsibility: Auth API operations.
 */

import { authAPI } from '@/api/auth'
import i18n from '@/i18n'
import { trackAuth, trackSegment } from '@/utils/telemetryTracker'
import { mapLoginError, mapRegisterError, mapPasswordError } from './authHelpers'
import { useCapabilitiesStore } from '@/stores/capabilitiesStore'

/**
 * Create auth action handlers
 * @param {Object} state - State refs
 * @returns {Object} Auth actions
 */
export function createAuthActions(state) {
  const { user, isAuthenticated, isLoading, error, authInitStarted, authInitialized } = state

  /**
   * Initialize auth state by checking token validity.
   *
   * Race fix: previously authInitialized was flipped to true synchronously
   * at the start, so waitForAuth() could resolve via its 5s timeout while
   * /auth/me was still in flight on slow cold starts — leaving user.value
   * null and downstream guards like `if (!userStore.userId) return` to
   * silently skip. Pages then rendered empty until you navigated away and
   * back. authInitStarted is the dedup guard now; authInitialized only
   * flips after user has been resolved.
   */
  async function initAuth() {
    if (authInitStarted.value || authInitialized.value) return

    authInitStarted.value = true
    isLoading.value = true

    try {
      const validUser = await authAPI.waitForAuth()

      if (validUser) {
        user.value = validUser
        isAuthenticated.value = true
        // Reload capabilities with fresh auth token (may have expired since first load)
        try { useCapabilitiesStore().reload() } catch {}
      } else {
        user.value = null
        isAuthenticated.value = false
      }
    } catch (e) {
      user.value = null
      isAuthenticated.value = false
      authAPI.clearAuth()
    } finally {
      isLoading.value = false
      authInitialized.value = true
    }
  }

  /**
   * Initialize user state from localStorage
   */
  function init() {
    if (authAPI.isLoggedIn()) {
      const localUser = authAPI.getLocalUser()
      if (localUser && !user.value) {
        user.value = localUser
        isAuthenticated.value = true
      }
    }
    initAuth()
  }

  /**
   * Login
   */
  async function login(email, password) {
    isLoading.value = true
    error.value = null

    try {
      const data = await authAPI.login(email, password)
      user.value = data.user
      isAuthenticated.value = true
      // Reload capabilities with fresh auth token
      try { useCapabilitiesStore().reload() } catch {}

      trackAuth.login('email')
      // Note: data.user is normalized to camelCase by auth.js
      const segment = data.user?.subscriptionPlan || 'free'
      const plan = data.user?.subscriptionStatus || null
      trackSegment.identifyUser(data.user?.id, segment, plan)

      return data
    } catch (err) {
      error.value = mapLoginError(err.message || '')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Google Login
   */
  async function googleLogin(credential) {
    isLoading.value = true
    error.value = null

    try {
      const data = await authAPI.googleLogin(credential)
      user.value = data.user
      isAuthenticated.value = true
      try { useCapabilitiesStore().reload() } catch {}

      trackAuth.login('google')
      const segment = data.user?.subscriptionPlan || 'free'
      const plan = data.user?.subscriptionStatus || null
      trackSegment.identifyUser(data.user?.id, segment, plan)

      return data
    } catch (err) {
      error.value = mapLoginError(err.message || '')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * GitHub Login
   */
  async function githubLogin(code) {
    isLoading.value = true
    error.value = null

    try {
      const data = await authAPI.githubLogin(code)
      user.value = data.user
      isAuthenticated.value = true
      try { useCapabilitiesStore().reload() } catch {}

      trackAuth.login('github')
      const segment = data.user?.subscriptionPlan || 'free'
      const plan = data.user?.subscriptionStatus || null
      trackSegment.identifyUser(data.user?.id, segment, plan)

      return data
    } catch (err) {
      error.value = mapLoginError(err.message || '')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Desktop OAuth (Tauri server-side flow)
   */
  async function desktopOAuth(provider) {
    isLoading.value = true
    error.value = null

    try {
      const data = await authAPI.startDesktopOAuth(provider)
      user.value = data.user
      isAuthenticated.value = true
      try { useCapabilitiesStore().reload() } catch {}

      trackAuth.login(provider)
      const segment = data.user?.subscriptionPlan || 'free'
      const plan = data.user?.subscriptionStatus || null
      trackSegment.identifyUser(data.user?.id, segment, plan)

      return data
    } catch (err) {
      error.value = mapLoginError(err.message || '')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Register
   */
  async function register(username, email, password) {
    isLoading.value = true
    error.value = null

    try {
      const data = await authAPI.register(username, email, password)
      user.value = data.user
      isAuthenticated.value = true

      trackAuth.register('email')
      // Note: data.user is normalized to camelCase by auth.js
      const userId = data.user?.id
      trackSegment.identifyUser(userId, 'free', null)
      trackSegment.signupCohort(userId, new Date().toISOString().split('T')[0], 'direct')

      return data
    } catch (err) {
      error.value = mapRegisterError(err.message || '')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Logout — clears store AND capabilities so no stale permission state
   * survives into the next login. authAPI.logout() ultimately redirects to
   * /login, but if navigation is delayed (slow network, modal mid-flight)
   * we want the in-memory state already dead.
   */
  async function logout() {
    trackAuth.logout()
    user.value = null
    isAuthenticated.value = false
    error.value = null
    try {
      // Lazy import to avoid a store ↔ store cycle.
      const { useCapabilitiesStore } = await import('@/stores/capabilitiesStore')
      useCapabilitiesStore().reset?.()
    } catch {
      // capabilities store didn't expose reset — ignore.
    }
    await authAPI.logout()
  }

  /**
   * Fetch current user info
   */
  async function fetchCurrentUser() {
    isLoading.value = true
    error.value = null

    try {
      const data = await authAPI.getCurrentUser()
      user.value = data
      isAuthenticated.value = true
      return data
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchUserInfo')
      user.value = null
      isAuthenticated.value = false
      authAPI.clearAuth()
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Change password
   */
  async function changePassword(oldPassword, newPassword) {
    isLoading.value = true
    error.value = null

    try {
      const data = await authAPI.changePassword(oldPassword, newPassword)
      return data
    } catch (err) {
      error.value = mapPasswordError(err.message || '')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  return {
    initAuth,
    init,
    login,
    googleLogin,
    githubLogin,
    desktopOAuth,
    register,
    logout,
    fetchCurrentUser,
    changePassword
  }
}
