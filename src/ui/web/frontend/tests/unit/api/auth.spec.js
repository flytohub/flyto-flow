import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock client
vi.mock('@/api/client', () => ({
  get: vi.fn(),
  post: vi.fn()
}))

vi.mock('@/api/config', () => ({
  STORAGE_KEYS: {
    ACCESS_TOKEN: 'access_token',
    REFRESH_TOKEN: 'refresh_token',
    USER: 'user'
  },
  ENDPOINTS: {
    AUTH: {
      LOGIN: '/auth/login',
      REGISTER: '/auth/register',
      LOGOUT: '/auth/logout',
      ME: '/auth/me',
      CHANGE_PASSWORD: '/auth/change-password',
      CONFIG: '/auth/config',
      GOOGLE_LOGIN: '/auth/google-login',
      GITHUB_LOGIN: '/auth/github-login',
      LINKED_PROVIDERS: '/auth/linked-providers',
      LINK_GOOGLE: '/auth/link-google',
      UNLINK_PROVIDER: '/auth/unlink-provider'
    }
  }
}))

vi.mock('@/config/defaults', () => ({
  DEFAULTS: {
    TIMEOUTS: {
      AUTH_CACHE_TTL: 60000
    }
  }
}))

vi.mock('@/i18n', () => ({
  default: {
    global: {
      t: vi.fn((key) => key)
    }
  }
}))

import { get, post } from '@/api/client'
import { authAPI } from '@/api/auth'

describe('Auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    // Reset the auth cache by calling clearAuth
    authAPI.clearAuth()
  })

  // =========================================================================
  // login
  // =========================================================================

  describe('login()', () => {
    it('calls POST /auth/login with email and password', async () => {
      post.mockResolvedValue({
        ok: true,
        user: { id: 'u1', email: 'user@flyto2.com', display_name: 'User' },
        accessToken: 'tok',
        refreshToken: 'ref'
      })

      const result = await authAPI.login('user@flyto2.com', 'pass123')

      expect(post).toHaveBeenCalledWith('/auth/login', { email: 'user@flyto2.com', password: 'pass123' })
      expect(result.user.email).toBe('user@flyto2.com')
      expect(result.accessToken).toBe('tok')
      expect(result.refreshToken).toBe('ref')
    })

    it('stores tokens and user in localStorage', async () => {
      post.mockResolvedValue({
        ok: true,
        user: { id: 'u1', email: 'user@flyto2.com' },
        accessToken: 'tok',
        refreshToken: 'ref'
      })

      await authAPI.login('user@flyto2.com', 'pass123')

      expect(localStorage.getItem('access_token')).toBe('tok')
      expect(localStorage.getItem('refresh_token')).toBe('ref')
      expect(JSON.parse(localStorage.getItem('user')).email).toBe('user@flyto2.com')
    })

    it('throws if email has no @ sign', async () => {
      await expect(authAPI.login('invalid', 'pass')).rejects.toThrow()
      expect(post).not.toHaveBeenCalled()
    })

    it('throws if response.ok is false', async () => {
      post.mockResolvedValue({ ok: false, error: 'Bad credentials' })

      await expect(authAPI.login('user@flyto2.com', 'wrong')).rejects.toThrow('Bad credentials')
    })

    it('returns mustChangePassword when set', async () => {
      post.mockResolvedValue({
        ok: true,
        user: { id: 'u1', email: 'user@flyto2.com' },
        accessToken: 'tok',
        mustChangePassword: true
      })

      const result = await authAPI.login('user@flyto2.com', 'pass')
      expect(result.mustChangePassword).toBe(true)
    })
  })

  // =========================================================================
  // register
  // =========================================================================

  describe('register()', () => {
    it('calls POST /auth/register with username, email, password', async () => {
      post.mockResolvedValue({
        ok: true,
        user: { id: 'u2', email: 'new@flyto2.com' },
        accessToken: 'tok2',
        refreshToken: 'ref2'
      })

      const result = await authAPI.register('newuser', 'new@flyto2.com', 'pass456')

      expect(post).toHaveBeenCalledWith('/auth/register', {
        email: 'new@flyto2.com',
        password: 'pass456',
        username: 'newuser'
      })
      expect(result.user.email).toBe('new@flyto2.com')
      expect(result.accessToken).toBe('tok2')
    })

    it('stores tokens in localStorage after registration', async () => {
      post.mockResolvedValue({
        ok: true,
        user: { id: 'u2', email: 'new@flyto2.com' },
        accessToken: 'tok2',
        refreshToken: 'ref2'
      })

      await authAPI.register('newuser', 'new@flyto2.com', 'pass456')

      expect(localStorage.getItem('access_token')).toBe('tok2')
      expect(localStorage.getItem('refresh_token')).toBe('ref2')
    })

    it('throws if response.ok is false', async () => {
      post.mockResolvedValue({ ok: false, error: 'Email already exists' })

      await expect(authAPI.register('u', 'dup@flyto2.com', 'p')).rejects.toThrow('Email already exists')
    })
  })

  // =========================================================================
  // logout
  // =========================================================================

  describe('logout()', () => {
    it('calls POST /auth/logout and clears localStorage', async () => {
      post.mockResolvedValue({})
      // Prevent actual redirect
      delete window.location
      window.location = { href: '' }

      localStorage.setItem('access_token', 'tok')
      localStorage.setItem('refresh_token', 'ref')
      localStorage.setItem('user', '{}')

      await authAPI.logout()

      expect(post).toHaveBeenCalledWith('/auth/logout')
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
      expect(window.location.href).toBe('/login')
    })

    it('clears localStorage even if API call fails', async () => {
      post.mockRejectedValue(new Error('Network Error'))
      delete window.location
      window.location = { href: '' }

      localStorage.setItem('access_token', 'tok')

      await authAPI.logout()

      expect(localStorage.getItem('access_token')).toBeNull()
      expect(window.location.href).toBe('/login')
    })
  })

  // =========================================================================
  // getCurrentUser
  // =========================================================================

  describe('getCurrentUser()', () => {
    it('calls GET /auth/me and returns normalized user', async () => {
      localStorage.setItem('access_token', 'tok')
      get.mockResolvedValue({
        id: 'u1',
        email: 'user@flyto2.com',
        displayName: 'Test User',
        isAdmin: false
      })

      const user = await authAPI.getCurrentUser(true)

      expect(get).toHaveBeenCalledWith('/auth/me')
      expect(user.email).toBe('user@flyto2.com')
      expect(user.displayName).toBe('Test User')
      expect(user.role).toBe('user')
    })

    it('throws if no access token in localStorage', async () => {
      await expect(authAPI.getCurrentUser()).rejects.toThrow()
      expect(get).not.toHaveBeenCalled()
    })

    it('returns cached user within TTL without making API call', async () => {
      localStorage.setItem('access_token', 'tok')
      get.mockResolvedValue({ id: 'u1', email: 'user@flyto2.com' })

      // First call fetches from API
      await authAPI.getCurrentUser(true)
      expect(get).toHaveBeenCalledTimes(1)

      // Second call should use cache (no forceRefresh)
      await authAPI.getCurrentUser(false)
      expect(get).toHaveBeenCalledTimes(1) // Still 1
    })

    it('normalizes admin user role', async () => {
      localStorage.setItem('access_token', 'tok')
      get.mockResolvedValue({ id: 'u1', email: 'admin@flyto2.com', isAdmin: true })

      const user = await authAPI.getCurrentUser(true)
      expect(user.role).toBe('admin')
      expect(user.isAdmin).toBe(true)
    })
  })

  // =========================================================================
  // changePassword
  // =========================================================================

  describe('changePassword()', () => {
    it('calls POST /auth/change-password with currentPassword and newPassword', async () => {
      post.mockResolvedValue({ ok: true })

      const result = await authAPI.changePassword('old', 'new')

      expect(post).toHaveBeenCalledWith('/auth/change-password', {
        currentPassword: 'old',
        newPassword: 'new'
      })
      expect(result.message).toBeDefined()
    })

    it('throws if response.ok is false', async () => {
      post.mockResolvedValue({ ok: false, error: 'Incorrect password' })

      await expect(authAPI.changePassword('wrong', 'new')).rejects.toThrow('Incorrect password')
    })
  })

  // =========================================================================
  // googleLogin
  // =========================================================================

  describe('googleLogin()', () => {
    it('calls POST /auth/google-login with credential', async () => {
      post.mockResolvedValue({
        ok: true,
        user: { id: 'g1', email: 'dev@flyto2.com' },
        accessToken: 'gTok',
        refreshToken: 'gRef'
      })

      const result = await authAPI.googleLogin('google-jwt-token')

      expect(post).toHaveBeenCalledWith('/auth/google-login', { credential: 'google-jwt-token' })
      expect(result.user.email).toBe('dev@flyto2.com')
      expect(localStorage.getItem('access_token')).toBe('gTok')
    })

    it('throws if response has no access token', async () => {
      post.mockResolvedValue({ ok: true, user: { id: 'g1' } })

      await expect(authAPI.googleLogin('jwt')).rejects.toThrow('no access token')
    })

    it('throws if response.ok is false', async () => {
      post.mockResolvedValue({ ok: false, error: 'Invalid token' })

      await expect(authAPI.googleLogin('bad')).rejects.toThrow('Invalid token')
    })
  })

  // =========================================================================
  // githubLogin
  // =========================================================================

  describe('githubLogin()', () => {
    it('calls POST /auth/github-login with code', async () => {
      post.mockResolvedValue({
        ok: true,
        user: { id: 'gh1', email: 'github@flyto2.com' },
        accessToken: 'ghTok',
        refreshToken: 'ghRef'
      })

      const result = await authAPI.githubLogin('gh-auth-code')

      expect(post).toHaveBeenCalledWith('/auth/github-login', { code: 'gh-auth-code' })
      expect(result.user.email).toBe('github@flyto2.com')
      expect(localStorage.getItem('access_token')).toBe('ghTok')
    })

    it('throws if response has no access token', async () => {
      post.mockResolvedValue({ ok: true, user: { id: 'gh1' } })

      await expect(authAPI.githubLogin('code')).rejects.toThrow('no access token')
    })
  })

  // =========================================================================
  // getAuthConfig
  // =========================================================================

  describe('getAuthConfig()', () => {
    it('calls GET /auth/config', async () => {
      get.mockResolvedValue({
        google: { enabled: true, clientId: 'gid' },
        github: { enabled: false }
      })

      const config = await authAPI.getAuthConfig()

      expect(get).toHaveBeenCalledWith('/auth/config')
      expect(config.google.enabled).toBe(true)
    })

    it('returns fallback on error (fresh module)', async () => {
      // getAuthConfig caches at module level, so use resetModules for a clean state
      vi.resetModules()
      const { get: freshGet } = await import('@/api/client')
      const freshAuth = await import('@/api/auth')
      freshGet.mockRejectedValue(new Error('Network Error'))

      const config = await freshAuth.authAPI.getAuthConfig()

      expect(config.google.enabled).toBe(false)
      expect(config.github.enabled).toBe(false)
      expect(config.allowSelfSignup).toBe(true)
    })
  })

  // =========================================================================
  // getLinkedProviders
  // =========================================================================

  describe('getLinkedProviders()', () => {
    it('calls GET /auth/linked-providers and returns array', async () => {
      get.mockResolvedValue({ providers: ['password', 'google.com'] })

      const providers = await authAPI.getLinkedProviders()

      expect(get).toHaveBeenCalledWith('/auth/linked-providers')
      expect(providers).toEqual(['password', 'google.com'])
    })

    it('returns empty array if no providers field', async () => {
      get.mockResolvedValue({})

      const providers = await authAPI.getLinkedProviders()
      expect(providers).toEqual([])
    })
  })

  // =========================================================================
  // linkGoogle / unlinkProvider
  // =========================================================================

  describe('linkGoogle()', () => {
    it('calls POST /auth/link-google with credential', async () => {
      post.mockResolvedValue({ ok: true, providers: ['password', 'google.com'] })

      const result = await authAPI.linkGoogle('jwt')

      expect(post).toHaveBeenCalledWith('/auth/link-google', { credential: 'jwt' })
      expect(result).toEqual(['password', 'google.com'])
    })

    it('throws if response.ok is false', async () => {
      post.mockResolvedValue({ ok: false, error: 'Already linked' })

      await expect(authAPI.linkGoogle('jwt')).rejects.toThrow('Already linked')
    })
  })

  describe('unlinkProvider()', () => {
    it('calls POST /auth/unlink-provider with providerId', async () => {
      post.mockResolvedValue({ ok: true, providers: ['password'] })

      const result = await authAPI.unlinkProvider('google.com')

      expect(post).toHaveBeenCalledWith('/auth/unlink-provider', { providerId: 'google.com' })
      expect(result).toEqual(['password'])
    })
  })

  // =========================================================================
  // isLoggedIn / getLocalUser / clearAuth
  // =========================================================================

  // Small helper — makes a JWT with the given exp claim. Unsigned; signature
  // is a throwaway string since our client never verifies it.
  const makeJwt = (exp) => {
    const b64url = (obj) =>
      btoa(JSON.stringify(obj)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
    return `${b64url({ alg: 'none', typ: 'JWT' })}.${b64url({ sub: 'u', exp })}.sig`
  }

  describe('isLoggedIn()', () => {
    it('returns true for a JWT whose exp is still in the future', () => {
      const future = Math.floor(Date.now() / 1000) + 3600
      localStorage.setItem('access_token', makeJwt(future))
      expect(authAPI.isLoggedIn()).toBe(true)
    })

    it('returns false AND purges the token when exp is in the past', () => {
      const past = Math.floor(Date.now() / 1000) - 3600
      localStorage.setItem('access_token', makeJwt(past))
      expect(authAPI.isLoggedIn()).toBe(false)
      // Expired token is cleaned up so the next call is honest.
      expect(localStorage.getItem('access_token')).toBeNull()
    })

    it('returns false AND purges a malformed token string', () => {
      localStorage.setItem('access_token', 'not-a-jwt')
      expect(authAPI.isLoggedIn()).toBe(false)
      expect(localStorage.getItem('access_token')).toBeNull()
    })

    it('returns false when no access_token', () => {
      expect(authAPI.isLoggedIn()).toBe(false)
    })

    it('trusts an opaque token without exp claim (back-compat)', () => {
      // Payload with no exp: treated as valid so legacy deployments don't
      // force-logout everyone.
      const b64url = (obj) =>
        btoa(JSON.stringify(obj)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
      const noExp = `${b64url({ alg: 'none', typ: 'JWT' })}.${b64url({ sub: 'u' })}.sig`
      localStorage.setItem('access_token', noExp)
      expect(authAPI.isLoggedIn()).toBe(true)
    })
  })

  describe('getAccessToken()', () => {
    it('returns the raw token when still valid', () => {
      const future = Math.floor(Date.now() / 1000) + 3600
      const tok = makeJwt(future)
      localStorage.setItem('access_token', tok)
      expect(authAPI.getAccessToken()).toBe(tok)
    })

    it('returns null AND purges an expired token', () => {
      const past = Math.floor(Date.now() / 1000) - 3600
      localStorage.setItem('access_token', makeJwt(past))
      expect(authAPI.getAccessToken()).toBeNull()
      expect(localStorage.getItem('access_token')).toBeNull()
    })

    it('returns null when no token exists', () => {
      expect(authAPI.getAccessToken()).toBeNull()
    })
  })

  describe('clearAuth()', () => {
    it('removes all three storage keys + resets cache', () => {
      localStorage.setItem('access_token', 'a')
      localStorage.setItem('refresh_token', 'r')
      localStorage.setItem('user', '{}')
      authAPI.clearAuth()
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
    })
  })

  describe('getLocalUser()', () => {
    it('returns parsed user from localStorage', () => {
      localStorage.setItem('user', JSON.stringify({ id: 'u1', email: 'user@flyto2.com' }))

      const user = authAPI.getLocalUser()
      expect(user.id).toBe('u1')
      expect(user.email).toBe('user@flyto2.com')
    })

    it('returns null if no user in localStorage', () => {
      expect(authAPI.getLocalUser()).toBeNull()
    })

    it('returns null if user JSON is invalid', () => {
      localStorage.setItem('user', 'invalid-json')
      expect(authAPI.getLocalUser()).toBeNull()
    })
  })

  describe('clearAuth()', () => {
    it('removes all auth data from localStorage', () => {
      localStorage.setItem('access_token', 'tok')
      localStorage.setItem('refresh_token', 'ref')
      localStorage.setItem('user', '{}')

      authAPI.clearAuth()

      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
    })
  })
})
