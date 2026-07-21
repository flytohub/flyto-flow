/**
 * githubAuth Unit Tests
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('githubAuth', () => {
  let setGithubClientId
  let isGithubAuthEnabled
  let requestGithubCredential
  let originalOpen
  let originalAddEventListener
  let originalRemoveEventListener

  beforeEach(async () => {
    // Reset modules to get fresh _clientId state each time
    vi.resetModules()
    const mod = await import('@/services/githubAuth')
    setGithubClientId = mod.setGithubClientId
    isGithubAuthEnabled = mod.isGithubAuthEnabled
    requestGithubCredential = mod.requestGithubCredential

    originalOpen = window.open
    originalAddEventListener = window.addEventListener
    originalRemoveEventListener = window.removeEventListener

    vi.spyOn(crypto, 'randomUUID').mockReturnValue('mock-uuid-1234')
    vi.useFakeTimers()
  })

  afterEach(() => {
    window.open = originalOpen
    window.addEventListener = originalAddEventListener
    window.removeEventListener = originalRemoveEventListener
    vi.restoreAllMocks()
    vi.useRealTimers()
    sessionStorage.clear()
    localStorage.clear()
  })

  // =========================================================================
  // setGithubClientId / isGithubAuthEnabled
  // =========================================================================

  describe('setGithubClientId', () => {
    it('should not overwrite with falsy values', () => {
      // VITE_GITHUB_CLIENT_ID is set in .env, so _clientId starts as truthy
      const wasBefore = isGithubAuthEnabled()
      setGithubClientId(null)
      setGithubClientId('')
      // State should remain unchanged (falsy values are ignored)
      expect(isGithubAuthEnabled()).toBe(wasBefore)
    })

    it('should set a valid client ID', () => {
      setGithubClientId('gh-client-123')
      expect(isGithubAuthEnabled()).toBe(true)
    })
  })

  describe('isGithubAuthEnabled', () => {
    it('should return true when client ID is configured', () => {
      setGithubClientId('test-env-client-id')
      expect(isGithubAuthEnabled()).toBe(true)
    })

    it('should return true after setting client ID', () => {
      setGithubClientId('test-client-id')
      expect(isGithubAuthEnabled()).toBe(true)
    })
  })

  // =========================================================================
  // requestGithubCredential
  // =========================================================================

  describe('requestGithubCredential', () => {
    it('should reject when popup is blocked', async () => {
      setGithubClientId('test-client-for-popup')
      window.open = vi.fn().mockReturnValue(null)
      await expect(requestGithubCredential()).rejects.toThrow('Popup blocked')
    })

    it('should reject when popup is blocked', async () => {
      setGithubClientId('gh-client-123')
      window.open = vi.fn().mockReturnValue(null)

      await expect(requestGithubCredential()).rejects.toThrow('Popup blocked')
    })

    it('should store OAuth state in sessionStorage', () => {
      setGithubClientId('gh-client-123')
      const mockPopup = { closed: false, close: vi.fn() }
      window.open = vi.fn().mockReturnValue(mockPopup)

      requestGithubCredential().catch(() => {}) // Don't care about rejection

      expect(sessionStorage.getItem('github_oauth_state')).toBe('mock-uuid-1234')
    })

    it('should open popup with correct URL', () => {
      setGithubClientId('gh-client-123')
      const mockPopup = { closed: false, close: vi.fn() }
      window.open = vi.fn().mockReturnValue(mockPopup)

      requestGithubCredential().catch(() => {})

      const callArgs = window.open.mock.calls[0]
      expect(callArgs[0]).toContain('github.com/login/oauth/authorize')
      expect(callArgs[0]).toContain('client_id=gh-client-123')
      expect(callArgs[0]).toContain('state=mock-uuid-1234')
      expect(callArgs[1]).toBe('github-oauth')
    })

    it('should resolve with code on successful postMessage', async () => {
      setGithubClientId('gh-client-123')
      const mockPopup = { closed: false, close: vi.fn() }
      window.open = vi.fn().mockReturnValue(mockPopup)

      let messageHandler
      window.addEventListener = vi.fn((event, handler) => {
        if (event === 'message') messageHandler = handler
      })
      window.removeEventListener = vi.fn()

      const promise = requestGithubCredential()

      // Simulate postMessage callback
      messageHandler({
        origin: window.location.origin,
        data: {
          type: 'github-oauth-callback',
          code: 'auth-code-xyz',
          state: 'mock-uuid-1234'
        }
      })

      const code = await promise
      expect(code).toBe('auth-code-xyz')
    })

    it('should reject on error from postMessage', async () => {
      setGithubClientId('gh-client-123')
      const mockPopup = { closed: false, close: vi.fn() }
      window.open = vi.fn().mockReturnValue(mockPopup)

      let messageHandler
      window.addEventListener = vi.fn((event, handler) => {
        if (event === 'message') messageHandler = handler
      })
      window.removeEventListener = vi.fn()

      const promise = requestGithubCredential()

      messageHandler({
        origin: window.location.origin,
        data: {
          type: 'github-oauth-callback',
          error: 'access_denied',
          state: 'mock-uuid-1234'
        }
      })

      await expect(promise).rejects.toThrow('access_denied')
    })

    it('should reject on invalid state parameter', async () => {
      setGithubClientId('gh-client-123')
      const mockPopup = { closed: false, close: vi.fn() }
      window.open = vi.fn().mockReturnValue(mockPopup)

      let messageHandler
      window.addEventListener = vi.fn((event, handler) => {
        if (event === 'message') messageHandler = handler
      })
      window.removeEventListener = vi.fn()

      const promise = requestGithubCredential()

      messageHandler({
        origin: window.location.origin,
        data: {
          type: 'github-oauth-callback',
          code: 'auth-code',
          state: 'wrong-state'
        }
      })

      await expect(promise).rejects.toThrow('Invalid state parameter')
    })

    it('should ignore messages from different origins', () => {
      setGithubClientId('gh-client-123')
      const mockPopup = { closed: false, close: vi.fn() }
      window.open = vi.fn().mockReturnValue(mockPopup)

      let messageHandler
      window.addEventListener = vi.fn((event, handler) => {
        if (event === 'message') messageHandler = handler
      })
      window.removeEventListener = vi.fn()

      requestGithubCredential().catch(() => {})

      // This message should be ignored (different origin)
      messageHandler({
        origin: 'https://evil.com',
        data: { type: 'github-oauth-callback', code: 'stolen' }
      })

      // The promise should not be resolved yet
      expect(sessionStorage.getItem('github_oauth_state')).toBe('mock-uuid-1234')
    })

    it('should ignore messages with wrong type', () => {
      setGithubClientId('gh-client-123')
      const mockPopup = { closed: false, close: vi.fn() }
      window.open = vi.fn().mockReturnValue(mockPopup)

      let messageHandler
      window.addEventListener = vi.fn((event, handler) => {
        if (event === 'message') messageHandler = handler
      })
      window.removeEventListener = vi.fn()

      requestGithubCredential().catch(() => {})

      messageHandler({
        origin: window.location.origin,
        data: { type: 'other-callback', code: 'wrong' }
      })

      // State should still be in sessionStorage (not resolved)
      expect(sessionStorage.getItem('github_oauth_state')).toBe('mock-uuid-1234')
    })
  })
})
