/**
 * Google Identity Services (GIS) integration
 *
 * Uses initTokenClient for custom button styling.
 * The access_token is sent to backend which calls Firebase signInWithIdp.
 *
 * Client ID is provided at runtime from the cloud auth config endpoint,
 * with fallback to VITE_GOOGLE_CLIENT_ID for local dev.
 */

const GIS_SCRIPT_URL = 'https://accounts.google.com/gsi/client'

let _clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || null
let _loadPromise = null
let _tokenClient = null
let _resolveAuth = null
let _rejectAuth = null

/**
 * Set Google client ID from cloud auth config (runtime).
 * @param {string} clientId
 */
export function setGoogleClientId(clientId) {
  if (clientId && clientId !== _clientId) {
    _clientId = clientId
    _tokenClient = null // Reset client to reinitialize with new ID
  }
}

/**
 * Check if Google OAuth is configured
 * @returns {boolean}
 */
export function isGoogleAuthEnabled() {
  return !!_clientId
}

/**
 * Load the Google Identity Services script
 * @returns {Promise<void>}
 */
function loadGisScript() {
  if (_loadPromise) return _loadPromise

  _loadPromise = new Promise((resolve, reject) => {
    if (window.google?.accounts?.oauth2) {
      resolve()
      return
    }

    const script = document.createElement('script')
    script.src = GIS_SCRIPT_URL
    script.async = true
    script.defer = true
    script.onload = resolve
    script.onerror = () => reject(new Error('Failed to load Google Identity Services'))
    document.head.appendChild(script)
  })

  return _loadPromise
}

/**
 * Ensure the token client is initialized
 */
function ensureTokenClient() {
  if (_tokenClient) return

  _tokenClient = window.google.accounts.oauth2.initTokenClient({
    client_id: _clientId,
    scope: 'openid email profile',
    callback: (response) => {
      if (response.access_token) {
        _resolveAuth?.(response.access_token)
      } else {
        _rejectAuth?.(new Error('Google authentication failed'))
      }
      _resolveAuth = null
      _rejectAuth = null
    },
    error_callback: (error) => {
      // popup_closed = user cancelled, not an error
      if (error.type === 'popup_closed') {
        _rejectAuth?.(null)
      } else {
        _rejectAuth?.(new Error(error.type || 'Google authentication failed'))
      }
      _resolveAuth = null
      _rejectAuth = null
    },
  })
}

/**
 * Open Google sign-in popup and return access token.
 * Rejects with null if user cancels (popup closed).
 * @returns {Promise<string>} Google access token
 */
export async function requestGoogleCredential() {
  if (!_clientId) throw new Error('Google OAuth not configured')

  await loadGisScript()
  ensureTokenClient()

  return new Promise((resolve, reject) => {
    _resolveAuth = resolve
    _rejectAuth = reject
    _tokenClient.requestAccessToken()
  })
}
