/**
 * Integration Test: Auth Flow
 *
 * Tests real auth flow through:
 * userStore -> authActions -> authAPI -> HTTP (mocked)
 *
 * localStorage interactions are REAL (jsdom provides them).
 * Only the HTTP client is mocked.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

// Mock the HTTP client at the boundary (not the auth API itself)
vi.mock('@/api/client', () => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  put: vi.fn(),
  del: vi.fn()
}))

// Mock i18n
vi.mock('@/i18n', () => ({
  default: {
    global: {
      t: (key) => key
    }
  }
}))

// Mock telemetry tracker (side-effect only)
vi.mock('@/utils/telemetryTracker', () => ({
  trackAuth: { login: vi.fn(), register: vi.fn(), logout: vi.fn() },
  trackSegment: { identifyUser: vi.fn(), signupCohort: vi.fn() }
}))

// Mock capabilities store (called during login to reload)
vi.mock('@/stores/capabilitiesStore', () => ({
  useCapabilitiesStore: () => ({
    reload: vi.fn()
  })
}))

// Mock config defaults — provide enough structure for all importers
vi.mock('@/config/defaults', () => ({
  DEFAULTS: {
    APP: { NAME: 'Flyto2', SUPPORT_EMAIL: '', WEBSITE: '', DOCS_URL: '' },
    HOME_STATS: { ACTIVE_USERS: 0, WORKFLOWS_CREATED: 0, SUCCESS_RATE: 0, TOTAL_EXECUTIONS: 0 },
    API: { PORT: 9000, HOST: '127.0.0.1', TIMEOUT: 30000, FALLBACK_URL: 'http://localhost:9000' },
    RETRY: { MAX_RETRIES: 3, DELAY: 1000, RETRYABLE_STATUSES: [408, 429, 500, 502, 503, 504] },
    TIMEOUTS: { AUTH_CACHE_TTL: 30000 }
  },
  getDefaultApiUrl: () => '',
  getWebSocketUrl: () => 'ws://localhost:9000'
}))

import { post, get } from '@/api/client'
import { useUserStore } from '@/stores/userStore'
import { mapLoginError, mapRegisterError, mapPasswordError } from '@/stores/user/authHelpers'

// Storage keys matching the real config (from @/config/api.js)
const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user'
}

describe('Auth Flow Integration', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    // Clear localStorage (REAL interactions)
    localStorage.clear()
    // Clear module-level auth cache in auth.js (persists across tests)
    window.dispatchEvent(new Event('auth-force-logout'))
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  // =========================================================================
  // Login Flow
  // =========================================================================

  describe('login flow', () => {
    it('should update store and localStorage on successful login', async () => {
      // Mock the POST /auth/login response
      post.mockResolvedValueOnce({
        ok: true,
        user: {
          id: 'user-001',
          email: 'test@flyto2.com',
          display_name: 'Test User',
          is_admin: false,
          is_pro: true,
          subscription_plan: 'pro',
          subscription_status: 'active'
        },
        accessToken: 'jwt-access-token-123',
        refreshToken: 'jwt-refresh-token-456'
      })

      store = useUserStore()
      const result = await store.login('test@flyto2.com', 'password123')

      // Verify store state (real Pinia reactivity)
      expect(store.isAuthenticated).toBe(true)
      expect(store.user).not.toBeNull()
      expect(store.user.email).toBe('test@flyto2.com')
      expect(store.user.displayName).toBe('Test User')
      expect(store.user.isPro).toBe(true)
      expect(store.user.isAdmin).toBe(false)

      // Verify real computed properties
      expect(store.username).toBe('Test User')
      expect(store.email).toBe('test@flyto2.com')
      expect(store.userId).toBe('user-001')
      expect(store.userRole).toBe('user')
      expect(store.isPro).toBe(true)
      expect(store.isAdmin).toBe(false)

      // Verify REAL localStorage was written
      const storedUser = JSON.parse(localStorage.getItem(STORAGE_KEYS.USER))
      expect(storedUser).not.toBeNull()
      expect(storedUser.email).toBe('test@flyto2.com')
      expect(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)).toBe('jwt-access-token-123')
      expect(localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)).toBe('jwt-refresh-token-456')

      // Verify loading state cleared
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('should handle login failure with real error mapping', async () => {
      post.mockResolvedValueOnce({
        ok: false,
        error: 'Invalid credentials'
      })

      store = useUserStore()

      await expect(store.login('wrong@flyto2.com', 'badpass')).rejects.toThrow()

      expect(store.isAuthenticated).toBe(false)
      expect(store.user).toBeNull()
      expect(store.error).toBeTruthy()
      expect(store.isLoading).toBe(false)

      // localStorage should NOT have tokens
      expect(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)).toBeNull()
    })
  })

  // =========================================================================
  // Register Flow
  // =========================================================================

  describe('register flow', () => {
    it('should register and populate store', async () => {
      post.mockResolvedValueOnce({
        ok: true,
        user: {
          id: 'user-002',
          email: 'newuser@flyto2.com',
          display_name: 'New User',
          is_admin: false,
          is_pro: false,
          subscription_plan: 'free'
        },
        accessToken: 'new-access-token',
        refreshToken: 'new-refresh-token'
      })

      store = useUserStore()
      await store.register('newuser', 'newuser@flyto2.com', 'securepass123')

      expect(store.isAuthenticated).toBe(true)
      expect(store.user.email).toBe('newuser@flyto2.com')
      expect(store.isPro).toBe(false)

      // REAL localStorage check
      expect(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)).toBe('new-access-token')
    })
  })

  // =========================================================================
  // Fetch Current User
  // =========================================================================

  describe('fetch current user', () => {
    it('should refresh user data from server', async () => {
      // Setup: user already logged in
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'existing-token')

      get.mockResolvedValueOnce({
        id: 'user-001',
        email: 'test@flyto2.com',
        display_name: 'Updated Name',
        is_admin: true,
        is_pro: true,
        roles: ['admin']
      })

      store = useUserStore()
      await store.fetchCurrentUser()

      expect(store.isAuthenticated).toBe(true)
      expect(store.user.displayName).toBe('Updated Name')
      expect(store.isAdmin).toBe(true)
      expect(store.userRole).toBe('admin')

      // localStorage should be updated
      const storedUser = JSON.parse(localStorage.getItem(STORAGE_KEYS.USER))
      expect(storedUser.displayName).toBe('Updated Name')
    })

    it('should clear auth on fetch failure (invalid token)', async () => {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'expired-token')

      get.mockRejectedValueOnce(new Error('Token expired'))

      store = useUserStore()

      await expect(store.fetchCurrentUser()).rejects.toThrow('Token expired')

      expect(store.isAuthenticated).toBe(false)
      expect(store.user).toBeNull()
      // Auth should be cleared
      expect(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)).toBeNull()
    })
  })

  // =========================================================================
  // Profile Update
  // =========================================================================

  describe('profile update', () => {
    it('should merge partial updates into user object', () => {
      store = useUserStore()
      store.user = {
        id: 'user-001',
        email: 'test@flyto2.com',
        displayName: 'Old Name',
        bio: 'Old bio'
      }
      store.isAuthenticated = true

      store.updateUser({ displayName: 'New Name', bio: 'New bio' })

      expect(store.user.displayName).toBe('New Name')
      expect(store.user.bio).toBe('New bio')
      expect(store.user.email).toBe('test@flyto2.com') // unchanged
      expect(store.username).toBe('New Name')
    })

    it('should not update if user is null', () => {
      store = useUserStore()
      store.updateUser({ displayName: 'Name' })
      expect(store.user).toBeNull()
    })
  })

  // =========================================================================
  // Logout -> cleanup
  // =========================================================================

  describe('logout flow', () => {
    it('should clear store and redirect', async () => {
      // Setup: user logged in
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'token')
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, 'refresh')
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify({ id: 'user-001' }))

      // Mock the logout POST (it silently fails)
      post.mockResolvedValueOnce({ ok: true })

      // Mock window.location
      const originalLocation = window.location
      delete window.location
      window.location = { href: '' }

      store = useUserStore()
      store.user = { id: 'user-001', email: 'test@flyto2.com' }
      store.isAuthenticated = true

      await store.logout()

      // Verify store cleared
      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.error).toBeNull()

      // Verify REAL localStorage cleared
      expect(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)).toBeNull()
      expect(localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)).toBeNull()
      expect(localStorage.getItem(STORAGE_KEYS.USER)).toBeNull()

      // Restore location
      window.location = originalLocation
    })
  })

  // =========================================================================
  // Auth error mappers (real, no mocks)
  // =========================================================================

  describe('auth error mappers (100% real)', () => {
    it('mapLoginError should map known error patterns', () => {
      expect(mapLoginError('invalid credentials')).toBe('Invalid email or password')
      expect(mapLoginError('user not found')).toBe('Invalid email or password')
      expect(mapLoginError('wrong password')).toBe('Invalid email or password')
      expect(mapLoginError('too many requests')).toBe('Too many attempts. Please try again later.')
      expect(mapLoginError('unknown error')).toBe('unknown error')
    })

    it('mapRegisterError should map known error patterns', () => {
      expect(mapRegisterError('email already exists')).toBe('Email already in use')
      expect(mapRegisterError('weak password')).toBe('Password is too weak (minimum 6 characters)')
      expect(mapRegisterError('invalid email format')).toBe('Invalid email format')
      expect(mapRegisterError('server error')).toBe('server error')
    })

    it('mapPasswordError should map known error patterns', () => {
      expect(mapPasswordError('current password incorrect')).toBe('Current password is incorrect')
      expect(mapPasswordError('wrong current password')).toBe('Current password is incorrect')
      expect(mapPasswordError('other error')).toBe('other error')
    })
  })

  // =========================================================================
  // Computed property behavior
  // =========================================================================

  describe('computed properties', () => {
    it('should derive username from displayName or email', () => {
      store = useUserStore()

      store.user = { email: 'john.doe@flyto2.com' }
      expect(store.username).toBe('john.doe')

      store.user = { email: 'john.doe@flyto2.com', displayName: 'John Doe' }
      expect(store.username).toBe('John Doe')

      store.user = null
      expect(store.username).toBe('')
    })

    it('should derive allowedLanguages based on auth and admin status', () => {
      store = useUserStore()

      // Not authenticated
      store.isAuthenticated = false
      expect(store.allowedLanguages).toBeNull()

      // Authenticated, admin
      store.isAuthenticated = true
      store.user = { isAdmin: true }
      expect(store.allowedLanguages).toBeNull()

      // Authenticated, non-admin, with restrictions
      store.user = { isAdmin: false, allowedLanguages: ['en', 'zh-TW'] }
      expect(store.allowedLanguages).toEqual(['en', 'zh-TW'])

      // Authenticated, non-admin, no restrictions
      store.user = { isAdmin: false }
      expect(store.allowedLanguages).toBeNull()
    })
  })

  // =========================================================================
  // Reset
  // =========================================================================

  describe('reset', () => {
    it('should clear all store state', () => {
      store = useUserStore()
      store.user = { id: 'user-001' }
      store.isAuthenticated = true
      store.error = 'some error'

      store.reset()

      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
    })
  })
})
