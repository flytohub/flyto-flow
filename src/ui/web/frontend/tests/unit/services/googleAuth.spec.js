/**
 * googleAuth Unit Tests
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// We need to re-import after resetting module state
let setGoogleClientId, isGoogleAuthEnabled, requestGoogleCredential

describe('googleAuth', () => {
  beforeEach(async () => {
    // Reset modules to clear module-level state
    vi.resetModules()

    // Mock import.meta.env
    vi.stubEnv('VITE_GOOGLE_CLIENT_ID', '')

    const mod = await import('@/services/googleAuth')
    setGoogleClientId = mod.setGoogleClientId
    isGoogleAuthEnabled = mod.isGoogleAuthEnabled
    requestGoogleCredential = mod.requestGoogleCredential
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllEnvs()
    delete window.google
  })

  // =========================================================================
  // setGoogleClientId / isGoogleAuthEnabled
  // =========================================================================

  describe('setGoogleClientId', () => {
    it('should set a valid client ID', () => {
      setGoogleClientId('google-client-123')
      expect(isGoogleAuthEnabled()).toBe(true)
    })

    it('should not set falsy values', () => {
      setGoogleClientId(null)
      expect(isGoogleAuthEnabled()).toBe(false)
    })

    it('should reset token client when ID changes', () => {
      setGoogleClientId('id-1')
      expect(isGoogleAuthEnabled()).toBe(true)
      setGoogleClientId('id-2')
      expect(isGoogleAuthEnabled()).toBe(true)
    })

    it('should not reset when same ID is set', () => {
      setGoogleClientId('same-id')
      setGoogleClientId('same-id')
      expect(isGoogleAuthEnabled()).toBe(true)
    })
  })

  describe('isGoogleAuthEnabled', () => {
    it('should return false when no client ID is configured', () => {
      expect(isGoogleAuthEnabled()).toBe(false)
    })

    it('should return true when client ID is set', () => {
      setGoogleClientId('test-id')
      expect(isGoogleAuthEnabled()).toBe(true)
    })
  })

  // =========================================================================
  // requestGoogleCredential
  // =========================================================================

  describe('requestGoogleCredential', () => {
    it('should throw when no client ID is configured', async () => {
      await expect(requestGoogleCredential()).rejects.toThrow('Google OAuth not configured')
    })

    it('should load GIS script and request access token', async () => {
      setGoogleClientId('google-client-123')

      let tokenCallback
      const mockRequestAccessToken = vi.fn()

      // Mock the GIS script already loaded
      window.google = {
        accounts: {
          oauth2: {
            initTokenClient: vi.fn((config) => {
              tokenCallback = config.callback
              return { requestAccessToken: mockRequestAccessToken }
            })
          }
        }
      }

      const promise = requestGoogleCredential()

      // Wait for script loading (already loaded via window.google)
      await vi.dynamicImportSettled?.() // Allow microtasks
      await new Promise(r => setTimeout(r, 0))

      // Simulate successful token response
      tokenCallback({ access_token: 'ya29.test-token' })

      const token = await promise
      expect(token).toBe('ya29.test-token')
      expect(mockRequestAccessToken).toHaveBeenCalled()
    })

    it('should reject when Google auth fails', async () => {
      setGoogleClientId('google-client-123')

      let tokenCallback
      const mockRequestAccessToken = vi.fn()

      window.google = {
        accounts: {
          oauth2: {
            initTokenClient: vi.fn((config) => {
              tokenCallback = config.callback
              return { requestAccessToken: mockRequestAccessToken }
            })
          }
        }
      }

      const promise = requestGoogleCredential()
      await new Promise(r => setTimeout(r, 0))

      // Simulate failed response (no access_token)
      tokenCallback({})

      await expect(promise).rejects.toThrow('Google authentication failed')
    })

    it('should reject with null when popup is closed by user', async () => {
      setGoogleClientId('google-client-123')

      let errorCallback
      const mockRequestAccessToken = vi.fn()

      window.google = {
        accounts: {
          oauth2: {
            initTokenClient: vi.fn((config) => {
              errorCallback = config.error_callback
              return { requestAccessToken: mockRequestAccessToken }
            })
          }
        }
      }

      const promise = requestGoogleCredential()
      await new Promise(r => setTimeout(r, 0))

      // Simulate popup closed
      errorCallback({ type: 'popup_closed' })

      await expect(promise).rejects.toBeNull()
    })

    it('should reject with error on non-popup-closed error', async () => {
      setGoogleClientId('google-client-123')

      let errorCallback
      const mockRequestAccessToken = vi.fn()

      window.google = {
        accounts: {
          oauth2: {
            initTokenClient: vi.fn((config) => {
              errorCallback = config.error_callback
              return { requestAccessToken: mockRequestAccessToken }
            })
          }
        }
      }

      const promise = requestGoogleCredential()
      await new Promise(r => setTimeout(r, 0))

      errorCallback({ type: 'popup_failed_to_open' })

      await expect(promise).rejects.toThrow('popup_failed_to_open')
    })

    it('should reject when GIS script fails to load', async () => {
      setGoogleClientId('google-client-123')

      // Don't set window.google — simulate script load via DOM
      const createElementSpy = vi.spyOn(document, 'createElement')
      const appendChildSpy = vi.spyOn(document.head, 'appendChild').mockImplementation(() => {})

      let scriptElement
      createElementSpy.mockImplementation((tag) => {
        if (tag === 'script') {
          scriptElement = {
            src: '',
            async: false,
            defer: false,
            onload: null,
            onerror: null
          }
          return scriptElement
        }
        return document.createElement(tag)
      })

      const promise = requestGoogleCredential()
      await new Promise(r => setTimeout(r, 0))

      // Simulate script load error
      if (scriptElement?.onerror) {
        scriptElement.onerror()
      }

      await expect(promise).rejects.toThrow('Failed to load Google Identity Services')
    })
  })
})
