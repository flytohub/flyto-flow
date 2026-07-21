import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock dependencies before importing stores
vi.mock('@/api/auth', () => ({
  authAPI: {
    login: vi.fn(),
    googleLogin: vi.fn(),
    githubLogin: vi.fn(),
    startDesktopOAuth: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    changePassword: vi.fn(),
    waitForAuth: vi.fn(),
    isLoggedIn: vi.fn(),
    getLocalUser: vi.fn(),
    clearAuth: vi.fn(),
  }
}))

vi.mock('@/i18n', () => ({
  default: {
    global: {
      t: (key) => key
    }
  }
}))

vi.mock('@/utils/telemetryTracker', () => ({
  trackAuth: { login: vi.fn(), register: vi.fn(), logout: vi.fn() },
  trackSegment: { identifyUser: vi.fn(), signupCohort: vi.fn() }
}))

vi.mock('@/stores/capabilitiesStore', () => ({
  useCapabilitiesStore: vi.fn(() => ({
    reload: vi.fn()
  }))
}))

import { useUserStore } from '@/stores/userStore'
import { authAPI } from '@/api/auth'

describe('useUserStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useUserStore()
    vi.clearAllMocks()
  })

  // ==========================================================================
  // Initial State
  // ==========================================================================
  describe('initial state', () => {
    it('has correct defaults', () => {
      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.isLoading).toBe(true)
      expect(store.error).toBeNull()
      expect(store.authInitialized).toBe(false)
    })
  })

  // ==========================================================================
  // Computed Getters
  // ==========================================================================
  describe('computed getters', () => {
    it('username falls back to email prefix when no displayName', () => {
      store.user = { email: 'john@flyto2.com' }
      expect(store.username).toBe('john')
    })

    it('username returns displayName when available', () => {
      store.user = { displayName: 'John Doe', email: 'john@flyto2.com' }
      expect(store.username).toBe('John Doe')
    })

    it('username returns empty string when no user', () => {
      store.user = null
      expect(store.username).toBe('')
    })

    it('email returns user email', () => {
      store.user = { email: 'john@flyto2.com' }
      expect(store.email).toBe('john@flyto2.com')
    })

    it('email returns empty string when no user', () => {
      expect(store.email).toBe('')
    })

    it('userId returns user id', () => {
      store.user = { id: 'user-123' }
      expect(store.userId).toBe('user-123')
    })

    it('userId returns null when no user', () => {
      expect(store.userId).toBeNull()
    })

    it('userRole defaults to "user"', () => {
      store.user = {}
      expect(store.userRole).toBe('user')
    })

    it('userRole returns the user role', () => {
      store.user = { role: 'admin' }
      expect(store.userRole).toBe('admin')
    })

    it('isAdmin is true only when backend says so', () => {
      store.user = { isAdmin: true }
      expect(store.isAdmin).toBe(true)
    })

    it('isAdmin is false when not set', () => {
      store.user = {}
      expect(store.isAdmin).toBe(false)
    })

    it('isPro requires both isAuthenticated and isPro flag', () => {
      store.user = { isPro: true }
      store.isAuthenticated = false
      expect(store.isPro).toBe(false)

      store.isAuthenticated = true
      expect(store.isPro).toBe(true)
    })

    it('allowedLanguages returns null when not authenticated (show all)', () => {
      store.isAuthenticated = false
      expect(store.allowedLanguages).toBeNull()
    })

    it('allowedLanguages returns null for admins (show all)', () => {
      store.isAuthenticated = true
      store.user = { isAdmin: true }
      expect(store.allowedLanguages).toBeNull()
    })

    it('allowedLanguages returns user list when set', () => {
      store.isAuthenticated = true
      store.user = { allowedLanguages: ['en', 'zh'] }
      expect(store.allowedLanguages).toEqual(['en', 'zh'])
    })
  })

  // ==========================================================================
  // Login Action
  // ==========================================================================
  describe('login', () => {
    it('sets user and isAuthenticated on success', async () => {
      const mockUser = { id: 'u1', email: 'test@flyto2.com', subscriptionPlan: 'pro' }
      authAPI.login.mockResolvedValue({ user: mockUser })

      await store.login('test@flyto2.com', 'password123')

      expect(store.user).toEqual(mockUser)
      expect(store.isAuthenticated).toBe(true)
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('sets error on failure and rethrows', async () => {
      authAPI.login.mockRejectedValue(new Error('invalid credentials'))

      await expect(store.login('bad@flyto2.com', 'wrong'))
        .rejects.toThrow('invalid credentials')

      expect(store.isAuthenticated).toBe(false)
      expect(store.error).toBe('Invalid email or password')
      expect(store.isLoading).toBe(false)
    })

    it('maps "too many" error correctly', async () => {
      authAPI.login.mockRejectedValue(new Error('too many attempts'))

      await expect(store.login('a@flyto2.com', 'c')).rejects.toThrow()
      expect(store.error).toBe('Too many attempts. Please try again later.')
    })
  })

  // ==========================================================================
  // Google Login
  // ==========================================================================
  describe('googleLogin', () => {
    it('sets user on success', async () => {
      const mockUser = { id: 'g1', email: 'google@flyto2.com' }
      authAPI.googleLogin.mockResolvedValue({ user: mockUser })

      await store.googleLogin('credential-token')

      expect(authAPI.googleLogin).toHaveBeenCalledWith('credential-token')
      expect(store.user).toEqual(mockUser)
      expect(store.isAuthenticated).toBe(true)
    })

    it('sets error on failure', async () => {
      authAPI.googleLogin.mockRejectedValue(new Error('invalid token'))

      await expect(store.googleLogin('bad-token')).rejects.toThrow()
      expect(store.error).toBe('Invalid email or password')
    })
  })

  // ==========================================================================
  // GitHub Login
  // ==========================================================================
  describe('githubLogin', () => {
    it('sets user on success', async () => {
      const mockUser = { id: 'gh1', email: 'github@flyto2.com' }
      authAPI.githubLogin.mockResolvedValue({ user: mockUser })

      await store.githubLogin('code-123')

      expect(authAPI.githubLogin).toHaveBeenCalledWith('code-123')
      expect(store.user).toEqual(mockUser)
      expect(store.isAuthenticated).toBe(true)
    })
  })

  // ==========================================================================
  // Desktop OAuth
  // ==========================================================================
  describe('desktopOAuth', () => {
    it('calls startDesktopOAuth with provider', async () => {
      const mockUser = { id: 'd1', email: 'desktop@flyto2.com' }
      authAPI.startDesktopOAuth.mockResolvedValue({ user: mockUser })

      await store.desktopOAuth('google')

      expect(authAPI.startDesktopOAuth).toHaveBeenCalledWith('google')
      expect(store.user).toEqual(mockUser)
      expect(store.isAuthenticated).toBe(true)
    })
  })

  // ==========================================================================
  // Register
  // ==========================================================================
  describe('register', () => {
    it('sets user on success', async () => {
      const mockUser = { id: 'r1', email: 'new@flyto2.com' }
      authAPI.register.mockResolvedValue({ user: mockUser })

      await store.register('newuser', 'new@flyto2.com', 'pass123')

      expect(authAPI.register).toHaveBeenCalledWith('newuser', 'new@flyto2.com', 'pass123')
      expect(store.user).toEqual(mockUser)
      expect(store.isAuthenticated).toBe(true)
    })

    it('maps "already exists" error', async () => {
      authAPI.register.mockRejectedValue(new Error('email already exists'))

      await expect(store.register('u', 'e@flyto2.com', 'p')).rejects.toThrow()
      expect(store.error).toBe('Email already in use')
    })

    it('maps "weak password" error', async () => {
      authAPI.register.mockRejectedValue(new Error('weak password'))

      await expect(store.register('u', 'e@flyto2.com', '1')).rejects.toThrow()
      expect(store.error).toBe('Password is too weak (minimum 6 characters)')
    })

    it('maps "invalid email" error', async () => {
      authAPI.register.mockRejectedValue(new Error('invalid email format'))

      await expect(store.register('u', 'bad', 'pass')).rejects.toThrow()
      expect(store.error).toBe('Invalid email format')
    })
  })

  // ==========================================================================
  // Logout
  // ==========================================================================
  describe('logout', () => {
    it('clears user state', async () => {
      store.user = { id: 'u1' }
      store.isAuthenticated = true

      authAPI.logout.mockResolvedValue()

      await store.logout()

      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  // ==========================================================================
  // Fetch Current User
  // ==========================================================================
  describe('fetchCurrentUser', () => {
    it('updates user on success', async () => {
      const mockUser = { id: 'u1', email: 'test@flyto2.com' }
      authAPI.getCurrentUser.mockResolvedValue(mockUser)

      const result = await store.fetchCurrentUser()

      expect(result).toEqual(mockUser)
      expect(store.user).toEqual(mockUser)
      expect(store.isAuthenticated).toBe(true)
    })

    it('clears auth and calls clearAuth on failure', async () => {
      authAPI.getCurrentUser.mockRejectedValue(new Error('Unauthorized'))

      await expect(store.fetchCurrentUser()).rejects.toThrow('Unauthorized')

      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(authAPI.clearAuth).toHaveBeenCalled()
    })
  })

  // ==========================================================================
  // Change Password
  // ==========================================================================
  describe('changePassword', () => {
    it('calls API on success', async () => {
      authAPI.changePassword.mockResolvedValue({ ok: true })

      const result = await store.changePassword('old', 'new')

      expect(authAPI.changePassword).toHaveBeenCalledWith('old', 'new')
      expect(result).toEqual({ ok: true })
    })

    it('maps "incorrect password" error', async () => {
      authAPI.changePassword.mockRejectedValue(new Error('incorrect password'))

      await expect(store.changePassword('wrong', 'new')).rejects.toThrow()
      expect(store.error).toBe('Current password is incorrect')
    })
  })

  // ==========================================================================
  // Init Auth
  // ==========================================================================
  describe('initAuth', () => {
    it('sets user when waitForAuth returns a user', async () => {
      const mockUser = { id: 'u1', email: 'test@flyto2.com' }
      authAPI.waitForAuth.mockResolvedValue(mockUser)

      await store.initAuth()

      expect(store.user).toEqual(mockUser)
      expect(store.isAuthenticated).toBe(true)
      expect(store.isLoading).toBe(false)
      expect(store.authInitialized).toBe(true)
    })

    it('clears user when waitForAuth returns null', async () => {
      authAPI.waitForAuth.mockResolvedValue(null)

      await store.initAuth()

      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.isLoading).toBe(false)
    })

    it('skips if already initialized', async () => {
      store.authInitialized = true

      await store.initAuth()

      expect(authAPI.waitForAuth).not.toHaveBeenCalled()
    })

    it('clears auth on error', async () => {
      authAPI.waitForAuth.mockRejectedValue(new Error('token expired'))

      await store.initAuth()

      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(authAPI.clearAuth).toHaveBeenCalled()
    })
  })

  // ==========================================================================
  // Init (from localStorage)
  // ==========================================================================
  describe('init', () => {
    it('hydrates from localStorage when logged in', async () => {
      authAPI.isLoggedIn.mockReturnValue(true)
      authAPI.getLocalUser.mockReturnValue({ id: 'u1', email: 'test@flyto2.com' })
      authAPI.waitForAuth.mockResolvedValue({ id: 'u1', email: 'test@flyto2.com' })

      store.init()

      expect(store.user).toEqual({ id: 'u1', email: 'test@flyto2.com' })
      expect(store.isAuthenticated).toBe(true)
    })

    it('does not hydrate when not logged in', async () => {
      authAPI.isLoggedIn.mockReturnValue(false)
      authAPI.waitForAuth.mockResolvedValue(null)

      store.init()

      expect(store.user).toBeNull()
    })
  })

  // ==========================================================================
  // Utility Actions
  // ==========================================================================
  describe('clearError', () => {
    it('clears the error', () => {
      store.error = 'Something went wrong'
      store.clearError()
      expect(store.error).toBeNull()
    })
  })

  describe('reset', () => {
    it('resets all state', () => {
      store.user = { id: 'u1' }
      store.isAuthenticated = true
      store.isLoading = true
      store.error = 'err'

      store.reset()

      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('updateUser', () => {
    it('merges data into existing user', () => {
      store.user = { id: 'u1', email: 'old@flyto2.com' }

      store.updateUser({ email: 'new@flyto2.com', displayName: 'New' })

      expect(store.user.email).toBe('new@flyto2.com')
      expect(store.user.displayName).toBe('New')
      expect(store.user.id).toBe('u1')
    })

    it('does nothing when user is null', () => {
      store.user = null
      store.updateUser({ email: 'test@flyto2.com' })
      expect(store.user).toBeNull()
    })
  })
})
