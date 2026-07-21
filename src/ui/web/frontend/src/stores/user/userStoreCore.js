/**
 * User Store Core
 *
 * S-Grade: Main user store using extracted auth actions.
 * Manages user state and authentication via Gateway API.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createAuthActions } from './authActions'
import { createAuthWaiter } from './authHelpers'

export const useUserStore = defineStore('user', () => {
  // ========== State ==========
  const user = ref(null)
  const isAuthenticated = ref(false)
  const isLoading = ref(true)
  const error = ref(null)
  // authInitStarted: set synchronously when initAuth() begins, used as a
  // dedup guard against concurrent inits.
  // authInitialized: set in initAuth()'s finally block — flips to true only
  // after user.value has been resolved (validated against /auth/me or set
  // to null on failure). waitForAuth polls on this flag, so consumers can
  // trust that userId is settled by the time waitForAuth resolves.
  const authInitStarted = ref(false)
  const authInitialized = ref(false)

  // ========== Getters ==========
  // Note: user data is always normalized to camelCase by auth.js
  const username = computed(() =>
    user.value?.displayName || user.value?.email?.split('@')[0] || ''
  )
  const email = computed(() => user.value?.email || '')
  const userId = computed(() => user.value?.id || null)
  const userRole = computed(() => user.value?.role || 'user')

  // S-Grade: Admin/Pro status MUST come from backend only
  const isAdmin = computed(() => user.value?.isAdmin === true)
  const isPro = computed(() => {
    if (!isAuthenticated.value) return false
    return user.value?.isPro === true
  })

  // S-Grade: Allowed languages from backend only
  // null = all languages allowed (admin or not set)
  const allowedLanguages = computed(() => {
    if (!isAuthenticated.value) return null  // Not logged in: show all
    if (isAdmin.value) return null  // Admin: show all
    return user.value?.allowedLanguages ?? null  // Default: show all
  })

  // ========== State refs for actions ==========
  const state = { user, isAuthenticated, isLoading, error, authInitStarted, authInitialized }

  // ========== Actions ==========
  const {
    initAuth, init, login, googleLogin, githubLogin, desktopOAuth, register, logout,
    fetchCurrentUser, changePassword
  } = createAuthActions(state)

  const waitForAuth = createAuthWaiter(isLoading, authInitialized)

  function clearError() {
    error.value = null
  }

  function reset() {
    user.value = null
    isAuthenticated.value = false
    isLoading.value = false
    error.value = null
  }

  function updateUser(userData) {
    if (user.value) {
      user.value = { ...user.value, ...userData }
    }
  }

  return {
    // State
    user, isAuthenticated, isLoading, error, authInitStarted, authInitialized,
    // Getters
    username, email, userId, userRole, isAdmin, isPro, allowedLanguages,
    // Actions
    init, initAuth, login, googleLogin, githubLogin, desktopOAuth, register, logout,
    fetchCurrentUser, changePassword, clearError, reset, waitForAuth, updateUser
  }
})
