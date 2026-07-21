/**
 * Authentication API — gateway-based, not Firebase SDK.
 *
 * ===========================================================================
 * Token storage security — READ BEFORE TOUCHING
 * ===========================================================================
 * Tokens live in localStorage, which is readable by any JavaScript in the
 * same origin (including a successful XSS payload). That's a deliberate,
 * documented trade-off: the desktop (Tauri) build doesn't have a cookie
 * jar shared with the backend, so the same code path has to work in both
 * browser and native contexts. Every non-desktop deployment is therefore
 * running with mitigations applied at other layers:
 *
 *   1. Strict CSP (default-src 'self'; no inline scripts; nonce'd where
 *      absolutely needed) — see Nginx / Cloud Run configs in
 *      src/ui/web/backend/...
 *   2. Dompurify on every v-html surface (audit has verified this).
 *   3. refresh-token rotation on every use — a stolen token's useful life
 *      is short. See client.js:handleUnauthorized + rotateRefreshToken.
 *   4. Cross-tab logout via BroadcastChannel so a forced clear propagates
 *      immediately.
 *   5. JWT exp validation in every authAPI.getAccessToken() call (stale
 *      tokens are purged before they leak into WebSockets, downloads,
 *      cross-product redirects).
 *
 * To migrate to httpOnly cookies later (recommended for
 * browser-only enterprise deployments):
 *   a) Backend sets Set-Cookie: access_token=...; HttpOnly; Secure;
 *      SameSite=Strict; Path=/ on login + refresh.
 *   b) Remove the manual Authorization header here; `withCredentials: true`
 *      already exists in client.js.
 *   c) Split the code path so desktop (Tauri) keeps using this localStorage
 *      variant — cookies don't round-trip between a Tauri webview and the
 *      external API host.
 *   d) Add a CSRF double-submit token since the browser now auto-attaches
 *      the cookie on every same-origin request.
 *
 * Don't piecemeal this — leaving localStorage in place while also setting
 * the cookie creates two sources of truth.
 * ===========================================================================
 */

import { post, get } from './client'
import { STORAGE_KEYS, ENDPOINTS } from './config'
import { DEFAULTS } from '@/config/defaults'
import i18n from '@/i18n'

// Auth state cache to prevent excessive /auth/me calls
let _authCache = {
  user: null,
  timestamp: 0,
  promise: null
}
const AUTH_CACHE_TTL = DEFAULTS.TIMEOUTS.AUTH_CACHE_TTL

// Clear auth cache when forced logout occurs (e.g. 401 redirect from client.js)
window.addEventListener('auth-force-logout', () => {
  _authCache.user = null
  _authCache.timestamp = 0
  _authCache.promise = null
})

// Cross-tab logout: BroadcastChannel is the primary signal, storage event is
// the fallback for browsers that don't support it (Safari < 15.4). When Tab A
// logs out, Tab B gets notified even though it doesn't share memory — both
// then drop their local auth cache and let the next navigation re-check.
const _authChannel = (typeof BroadcastChannel !== 'undefined')
  ? new BroadcastChannel('flyto.auth')
  : null

if (_authChannel) {
  _authChannel.addEventListener('message', (ev) => {
    if (ev.data?.type === 'logout') {
      _authCache.user = null
      _authCache.timestamp = 0
      _authCache.promise = null
      window.dispatchEvent(new Event('auth-force-logout'))
    }
  })
}

// storage-event fallback: fires when another tab removes ACCESS_TOKEN.
window.addEventListener('storage', (ev) => {
  if (ev.key === STORAGE_KEYS.ACCESS_TOKEN && ev.newValue === null && ev.oldValue) {
    _authCache.user = null
    _authCache.timestamp = 0
    _authCache.promise = null
    window.dispatchEvent(new Event('auth-force-logout'))
  }
})

/**
 * broadcastLogout — tell every tab in this origin that auth just ended.
 * Called from logout() and 401-force-logout so all tabs converge.
 */
function broadcastLogout() {
  try {
    _authChannel?.postMessage({ type: 'logout' })
  } catch {
    // Channel closed — storage event will still fire if tokens were cleared.
  }
}

/**
 * Normalize user object to camelCase
 * Handles both camelCase and snake_case input for backward compatibility
 * All output fields are guaranteed to be camelCase
 */
function normalizeUser(data) {
  if (!data) return null
  return {
    id: data.id,
    uid: data.id || data.uid,
    email: data.email,
    displayName: data.displayName ?? data.display_name ?? '',
    avatarUrl: data.avatarUrl ?? data.avatar_url ?? null,
    bio: data.bio ?? '',
    website: data.website ?? '',
    role: (data.isAdmin || data.is_admin) ? 'admin' : 'user',
    isAdmin: data.isAdmin ?? data.is_admin ?? false,
    isPro: data.isPro ?? data.is_pro ?? false,
    roles: data.roles ?? [],
    allowedLanguages: data.allowedLanguages ?? data.allowed_languages ?? null,
    subscriptionPlan: data.subscriptionPlan ?? data.subscription_plan ?? 'free',
    subscriptionStatus: data.subscriptionStatus ?? data.subscription_status ?? 'active',
    createdAt: data.createdAt ?? data.created_at ?? null,
    followersCount: data.followersCount ?? data.followers_count ?? 0,
    followingCount: data.followingCount ?? data.following_count ?? 0
  }
}

// Auth config cache (provider availability from cloud)
let _authConfigCache = null
let _authConfigPromise = null

export const authAPI = {
  /**
   * Get auth provider config from cloud (which OAuth providers are enabled + client IDs).
   * Cached for the session lifetime — provider config doesn't change at runtime.
   * @returns {Promise<Object>} { google: { enabled, clientId }, github: { enabled, clientId }, allowSelfSignup }
   */
  async getAuthConfig() {
    if (_authConfigCache) return _authConfigCache
    if (_authConfigPromise) return _authConfigPromise

    _authConfigPromise = (async () => {
      try {
        const data = await get(ENDPOINTS.AUTH.CONFIG)
        _authConfigCache = data
        return data
      } catch {
        // Cloud unreachable — fall back to disabled
        return { google: { enabled: false }, github: { enabled: false }, allowSelfSignup: true }
      } finally {
        _authConfigPromise = null
      }
    })()

    return _authConfigPromise
  },

  /**
   * Login with email and password
   * @param {string} email - Email
   * @param {string} password - Password
   * @returns {Promise<Object>} Login result with user info
   */
  async login(email, password) {
    // Validate email format
    if (!email.includes('@')) {
      throw new Error(i18n.global.t('error.useEmailToLogin'))
    }

    const response = await post(ENDPOINTS.AUTH.LOGIN, { email, password })

    if (!response.ok) {
      throw new Error(response.error || i18n.global.t('error.loginFailed'))
    }

    const user = normalizeUser(response.user)

    // Drop any stale tokens from a previous session before writing new ones —
    // if the new response omits `refreshToken`, we don't want the old one
    // surviving into the fresh session (root cause of the "stale refresh loop").
    this.clearAuth()

    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user))
    if (response.accessToken) {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.accessToken)
    }
    if (response.refreshToken) {
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.refreshToken)
    }

    return {
      user,
      mustChangePassword: response.mustChangePassword || false,
      accessToken: response.accessToken,
      refreshToken: response.refreshToken
    }
  },

  /**
   * Register new user
   * @param {string} username - Username
   * @param {string} email - Email
   * @param {string} password - Password
   * @returns {Promise<Object>} Registration result
   */
  async register(username, email, password) {
    const response = await post(ENDPOINTS.AUTH.REGISTER, {
      email,
      password,
      username
    })

    if (!response.ok) {
      throw new Error(response.error || i18n.global.t('error.registrationFailed'))
    }

    const user = normalizeUser(response.user)

    this.clearAuth()
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user))
    if (response.accessToken) {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.accessToken)
    }
    if (response.refreshToken) {
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.refreshToken)
    }

    return {
      user,
      accessToken: response.accessToken,
      refreshToken: response.refreshToken
    }
  },

  /**
   * Logout — always clears local state, even if the server call fails.
   * Broadcasts across tabs so every instance drops its in-memory auth.
   */
  async logout() {
    try {
      await post(ENDPOINTS.AUTH.LOGOUT)
    } catch (err) {
      // Network / server hiccup on the way out is non-fatal; we're leaving
      // the session anyway. Log for telemetry visibility, then fall through
      // to the local cleanup that actually matters.
      if (typeof console !== 'undefined') {
        // eslint-disable-next-line no-console
        console.warn('auth.logout: server call failed, clearing local state anyway', err)
      }
    }
    this.clearAuth()
    broadcastLogout()
    window.location.href = '/login'
  },

  /**
   * Get current user info (refresh from server)
   * Uses cache to prevent excessive /auth/me calls
   * @param {boolean} forceRefresh - Force refresh from server
   * @returns {Promise<Object>} User information
   */
  async getCurrentUser(forceRefresh = false) {
    const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
    if (!token) {
      throw new Error(i18n.global.t('error.notAuthenticated'))
    }

    const now = Date.now()

    // Return cached result if still valid
    if (!forceRefresh && _authCache.user && (now - _authCache.timestamp) < AUTH_CACHE_TTL) {
      return _authCache.user
    }

    // If a request is already in flight, wait for it
    if (_authCache.promise) {
      return _authCache.promise
    }

    // Make the request
    _authCache.promise = (async () => {
      try {
        const response = await get(ENDPOINTS.AUTH.ME)
        const user = normalizeUser(response.user || response)

        // Update localStorage and cache
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user))
        _authCache.user = user
        _authCache.timestamp = Date.now()

        return user
      } finally {
        _authCache.promise = null
      }
    })()

    return _authCache.promise
  },

  /**
   * Change password
   * @param {string} oldPassword - Old password
   * @param {string} newPassword - New password
   * @returns {Promise<Object>} Change result
   */
  async changePassword(oldPassword, newPassword) {
    const response = await post(ENDPOINTS.AUTH.CHANGE_PASSWORD, {
      currentPassword: oldPassword,
      newPassword
    })

    if (!response.ok) {
      throw new Error(response.error || i18n.global.t('error.passwordChangeFailed'))
    }

    return { message: i18n.global.t('message.passwordUpdated') }
  },

  /**
   * Login with Google credential
   * @param {string} credential - Google JWT from GIS callback
   * @returns {Promise<Object>} Login result with user info
   */
  async googleLogin(credential) {
    const response = await post(ENDPOINTS.AUTH.GOOGLE_LOGIN, { credential })

    if (!response.ok) {
      throw new Error(response.error || 'Google login failed')
    }

    // Validate that backend returned tokens
    if (!response.accessToken) {
      throw new Error('Google login failed: no access token received')
    }

    const user = normalizeUser(response.user)

    this.clearAuth()
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user))
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.accessToken)
    if (response.refreshToken) {
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.refreshToken)
    }

    return {
      user,
      accessToken: response.accessToken,
      refreshToken: response.refreshToken
    }
  },

  /**
   * Login with GitHub authorization code
   * @param {string} code - GitHub OAuth authorization code
   * @returns {Promise<Object>} Login result with user info
   */
  async githubLogin(code) {
    const response = await post(ENDPOINTS.AUTH.GITHUB_LOGIN, { code })

    if (!response.ok) {
      throw new Error(response.error || 'GitHub login failed')
    }

    if (!response.accessToken) {
      throw new Error('GitHub login failed: no access token received')
    }

    const user = normalizeUser(response.user)

    this.clearAuth()
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user))
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.accessToken)
    if (response.refreshToken) {
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.refreshToken)
    }

    return {
      user,
      accessToken: response.accessToken,
      refreshToken: response.refreshToken
    }
  },

  /**
   * Start server-side OAuth flow.
   * Desktop: sidecar opens system browser. Web: opens popup window.
   * Both poll backend for result after user authorizes.
   * @param {string} provider - 'google' or 'github'
   * @returns {Promise<Object>} Login result with user info
   */
  async startDesktopOAuth(provider) {
    const startResp = await get(`/auth/oauth/start?provider=${provider}`)
    if (!startResp.ok) throw new Error(startResp.error || 'Failed to start OAuth')

    const { state, url } = startResp

    // Web mode: open OAuth URL in popup (desktop sidecar opens system browser instead)
    const isDesktop = !!window.__TAURI_INTERNALS__
    let popup = null
    if (!isDesktop && url) {
      const w = 500, h = 700
      const left = window.screenX + (window.outerWidth - w) / 2
      const top = window.screenY + (window.outerHeight - h) / 2
      popup = window.open(url, 'oauth', `width=${w},height=${h},left=${left},top=${top}`)
    }

    // Poll every 2 seconds, max 5 minutes (150 iterations)
    for (let i = 0; i < 150; i++) {
      await new Promise(r => setTimeout(r, 2000))
      const result = await get(`/auth/oauth/poll?state=${state}`)

      if (result.status === 'complete') {
        if (popup) try { popup.close() } catch {}
        if (!result.ok) throw new Error(result.error || 'OAuth failed')

        const user = normalizeUser(result.user)
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user))
        if (result.accessToken) {
          localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, result.accessToken)
        }
        if (result.refreshToken) {
          localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, result.refreshToken)
        }
        return { user, accessToken: result.accessToken, refreshToken: result.refreshToken }
      }

      if (result.status === 'expired' || result.status === 'not_found') {
        if (popup) try { popup.close() } catch {}
        throw new Error('OAuth timed out or was cancelled')
      }

      // Close polling early if user closed the popup
      if (popup && popup.closed && i > 5) {
        throw new Error('OAuth cancelled')
      }
      // status === 'pending': continue polling
    }

    throw new Error('OAuth timed out')
  },

  /**
   * Get linked auth providers for current user
   * @returns {Promise<string[]>} Array of provider IDs
   */
  async getLinkedProviders() {
    const response = await get(ENDPOINTS.AUTH.LINKED_PROVIDERS)
    return response.providers || []
  },

  /**
   * Link Google account to current user
   * @param {string} credential - Google JWT from GIS callback
   * @returns {Promise<string[]>} Updated provider list
   */
  async linkGoogle(credential) {
    const response = await post(ENDPOINTS.AUTH.LINK_GOOGLE, { credential })
    if (!response.ok) {
      throw new Error(response.error || 'Failed to link Google account')
    }
    return response.providers || []
  },

  /**
   * Unlink a provider from current user
   * @param {string} providerId - Provider to unlink (e.g. "google.com")
   * @returns {Promise<string[]>} Updated provider list
   */
  async unlinkProvider(providerId) {
    const response = await post(ENDPOINTS.AUTH.UNLINK_PROVIDER, { providerId })
    if (!response.ok) {
      throw new Error(response.error || 'Failed to unlink provider')
    }
    return response.providers || []
  },

  /**
   * Returns the raw access token if present AND not expired; otherwise
   * returns null AND purges the stored token. Use this anywhere you were
   * reaching into `localStorage.access_token` directly — that pattern
   * skips the JWT validation that `isLoggedIn()` now does, which lets
   * stale/expired tokens leak into outbound API calls, WebSockets, and
   * cross-product redirects.
   *
   * @returns {string|null}
   */
  getAccessToken() {
    // isLoggedIn() decodes and purges — we reuse its validation logic.
    return this.isLoggedIn() ? localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN) : null
  },

  /**
   * Clear every piece of local auth state — tokens, user, cache.
   * Safe to call from anywhere (logout, refresh failure, 401 interceptor,
   * cross-tab sync). Does NOT redirect — caller decides.
   */
  clearAuth() {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.USER)
    _authCache.user = null
    _authCache.timestamp = 0
    _authCache.promise = null
  },

  /**
   * Check if user is logged in.
   *
   * Decodes the JWT payload and verifies `exp > now`. A missing, malformed,
   * or expired token is treated as logged-out AND eagerly removed from
   * localStorage so the next call doesn't have to re-parse it. This
   * prevents a stale/rotated token from keeping the router guard happy
   * while every backend call 401s — the bug that let `/` render blank
   * instead of redirecting to `/login`.
   *
   * The 30s clock-skew budget below is intentional — JWT exp is in
   * seconds and client clocks drift a few seconds; being strict here
   * would log people out a tick before the real expiry.
   *
   * @returns {boolean}
   */
  isLoggedIn() {
    const tok = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
    if (!tok) return false
    try {
      const parts = tok.split('.')
      if (parts.length !== 3) throw new Error('not a jwt')
      // base64url → base64
      const b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
      const padded = b64 + '='.repeat((4 - (b64.length % 4)) % 4)
      const payload = JSON.parse(atob(padded))
      if (typeof payload.exp !== 'number') return true // opaque token; trust it
      const nowSec = Math.floor(Date.now() / 1000)
      if (payload.exp <= nowSec - 30) {
        // Expired (with 30s skew) — purge so the next call is honest.
        localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
        return false
      }
      return true
    } catch {
      // Malformed — can't trust it; purge.
      localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
      return false
    }
  },

  /**
   * Get local user info (from localStorage)
   * Always returns normalized camelCase format
   * @returns {Object|null} User information
   */
  getLocalUser() {
    const user = localStorage.getItem(STORAGE_KEYS.USER)
    if (user) {
      try {
        // Normalize to ensure camelCase regardless of stored format
        return normalizeUser(JSON.parse(user))
      } catch {
        return null
      }
    }
    return null
  },

  /**
   * Wait for auth state to be ready
   * Uses cache to prevent excessive /auth/me calls
   * @returns {Promise<Object|null>} Current user or null
   */
  async waitForAuth() {
    const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
    if (!token) {
      return null
    }

    // Return cached user if still valid (prevents rate limiting)
    const now = Date.now()
    if (_authCache.user && (now - _authCache.timestamp) < AUTH_CACHE_TTL) {
      return _authCache.user
    }

    // Also check localStorage as fallback (faster than API call)
    const localUser = this.getLocalUser()
    if (localUser && !_authCache.user) {
      // Use local user if cache is empty - will refresh in background
      _authCache.user = localUser
      _authCache.timestamp = now - AUTH_CACHE_TTL + 2000 // Valid for 2 more seconds
    }

    try {
      const user = await this.getCurrentUser()
      return user
    } catch (error) {
      // If rate limited, use cached/local user
      if (error?.status === 429 && (_authCache.user || localUser)) {
        return _authCache.user || localUser
      }
      // Token invalid or expired
      _authCache.user = null
      _authCache.timestamp = 0
      localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
      localStorage.removeItem(STORAGE_KEYS.USER)
      return null
    }
  },

  /**
   * Clear all auth data
   */
  clearAuth() {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.USER)
    // Clear auth cache
    _authCache.user = null
    _authCache.timestamp = 0
    _authCache.promise = null
  }
}
