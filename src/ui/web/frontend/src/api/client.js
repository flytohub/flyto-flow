/**
 * API Client
 * Unified HTTP client for all API requests
 * Supports both Web and Electron environments
 */

import axios from 'axios'
import { API_URL, REQUEST_TIMEOUT, STORAGE_KEYS, ENDPOINTS } from './config'
import { isEncryptionEnabled, generateRequestKey, encryptPayload, decryptResponse } from '@/utils/payloadEncryption'
import { convertKeysToSnake, convertKeysToCamel } from './caseConversion'
import { enrichError, dispatchBusinessErrors, withRetry } from './errorHandling'

/**
 * Create Axios instance
 */
const client = axios.create({
  baseURL: API_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
})

// =============================================================================
// Telemetry Integration (Lazy Import)
// =============================================================================

// Lazy import to avoid circular dependency
let _telemetryModule = null
let _telemetryTrackerModule = null

async function getTelemetry() {
  if (!_telemetryModule) {
    _telemetryModule = await import('@/services/telemetry')
  }
  return _telemetryModule
}

async function getTrackUX() {
  if (!_telemetryTrackerModule) {
    _telemetryTrackerModule = await import('@/utils/telemetryTracker')
  }
  return _telemetryTrackerModule.trackUX
}

async function getTrackPerformance() {
  if (!_telemetryTrackerModule) {
    _telemetryTrackerModule = await import('@/utils/telemetryTracker')
  }
  return _telemetryTrackerModule.trackPerformance
}

// Threshold for slow API (2 seconds)
const SLOW_API_THRESHOLD = 2000

// Shared promise to deduplicate concurrent token refresh requests
let _refreshPromise = null

function isTelemetryRequest(url) {
  if (!url) return false
  const target = String(url)
  return target.includes('/telemetry')
}

/**
 * Request interceptor - Auto add auth token, dynamic base URL, case conversion, and telemetry
 */
client.interceptors.request.use(
  async (config) => {
    const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add user region header for marketplace filtering
    const userRegion = localStorage.getItem('user_region')
    if (userRegion) {
      config.headers['X-User-Region'] = userRegion
    }

    // Add telemetry headers (trace ID, session ID)
    try {
      const { telemetry } = await getTelemetry()
      config.headers['X-Trace-ID'] = telemetry.getTraceId()
      config.headers['X-Session-ID'] = telemetry.getSessionId()
    } catch {
      // Telemetry not available, continue without
    }

    // Record start time for duration tracking
    config._startTime = Date.now()

    // Convert request data from camelCase to snake_case (for backend)
    // Skip FormData - let axios handle Content-Type with boundary
    if (config.data && !(config.data instanceof FormData)) {
      config.data = convertKeysToSnake(config.data)
    } else if (config.data instanceof FormData) {
      // Remove Content-Type so axios sets it with correct boundary
      delete config.headers['Content-Type']
    }

    // Convert query params from camelCase to snake_case
    if (config.params) {
      config.params = convertKeysToSnake(config.params)
    }

    // Application-layer encryption (when PAYLOAD_ENCRYPTION=on in production)
    // Encrypts ALL requests (GET included) so responses are always encrypted.
    try {
      const enabled = await isEncryptionEnabled()
      if (enabled) {
        const reqKey = await generateRequestKey()
        if (reqKey) {
          // Send encrypted AES key in header (server uses it to encrypt response)
          config.headers['X-Enc-Key'] = reqKey.encKeyHeader
          config._aesKey = reqKey.aesKey

          // Encrypt request body for POST/PUT/PATCH
          if (config.data && !(config.data instanceof FormData)) {
            config.data = await encryptPayload(config.data, reqKey.aesKey)
          }
        }
      }
    } catch {
      // Encryption failed — send plaintext (defense in depth: TLS still protects)
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * Track response performance telemetry (slow API calls and sampling)
 */
async function trackResponsePerformance(response) {
  if (!response.config?._startTime) return

  response.config._duration = Date.now() - response.config._startTime

  // Track slow API calls (skip telemetry endpoint to avoid infinite loop)
  if (response.config._duration > SLOW_API_THRESHOLD &&
      !isTelemetryRequest(response.config.url)) {
    try {
      const trackPerformance = await getTrackPerformance()
      trackPerformance.slowApi(
        response.config.url,
        response.config.method?.toUpperCase() || 'GET',
        response.config._duration,
        response.status
      )
    } catch {
      // Telemetry not available, continue without
    }
  }

  // Track all API responses (10% sampling for performance monitoring)
  if (Math.random() < 0.1 && !isTelemetryRequest(response.config.url)) {
    try {
      const { telemetry } = await getTelemetry()
      telemetry.track('api.performance', {
        endpoint: response.config.url,
        method: response.config.method?.toUpperCase() || 'GET',
        status: response.status,
        duration_ms: response.config._duration,
        is_slow: response.config._duration > SLOW_API_THRESHOLD
      })
    } catch {
      // Telemetry not available, continue without
    }
  }
}

/**
 * Handle 401 unauthorized error - attempt token refresh before kicking user
 */
async function handleUnauthorized(error) {
  if (error.response?.status !== 401) return

  const requestUrl = error.config?.url || ''

  // Never retry refresh, auth/me, or login requests (avoid infinite loop)
  const noRetryPatterns = [ENDPOINTS.AUTH.REFRESH, ENDPOINTS.AUTH.ME, ENDPOINTS.AUTH.LOGIN, ENDPOINTS.AUTH.GOOGLE_LOGIN, ENDPOINTS.AUTH.GITHUB_LOGIN]
  const isNoRetry = noRetryPatterns.some(p => requestUrl.includes(p))

  if (!isNoRetry && !error.config._retried) {
    // Try to refresh the token (deduplicate concurrent 401s with shared promise)
    const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)
    if (refreshToken) {
      let refreshOk = false
      try {
        if (!_refreshPromise) {
          _refreshPromise = client.post(ENDPOINTS.AUTH.REFRESH, {
            refresh_token: refreshToken
          }).finally(() => { _refreshPromise = null })
        }
        const res = await _refreshPromise
        const data = res.data
        // Note: response interceptor converts snake_case -> camelCase
        const newAccessToken = data.accessToken || data.access_token
        const newRefreshToken = data.refreshToken || data.refresh_token
        if (data.ok && newAccessToken) {
          // Save new tokens. If the server did NOT rotate the refresh
          // token, drop the old one so the next 401 doesn't retry with a
          // known-stale credential — correct behaviour for servers that
          // rotate refresh on each use (BCP 287 / RFC 6819 §5.2.2.3).
          localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, newAccessToken)
          if (newRefreshToken) {
            localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, newRefreshToken)
          } else {
            localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
          }
          refreshOk = true
          // Retry the original request with new token
          error.config._retried = true
          error.config.headers.Authorization = `Bearer ${newAccessToken}`
          return client(error.config)
        }
      } catch {
        // Network / 5xx / parse failure — treat as full auth loss below.
      }
      // Refresh attempt returned non-ok or threw. In either case the
      // refresh token in localStorage is probably dead; purge so we fall
      // back to the login redirect without another loop.
      if (!refreshOk) {
        localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
      }
    }
  }

  // Refresh failed / absent — redirect to login. /capabilities and /chat/
  // used to be on this skip list; they came off because a 401 on
  // capabilities was masking real auth loss and leaving the user on a
  // blank page. Only the auth endpoints themselves stay skipped — those
  // are allowed to fail quietly (login form shows the error).
  const skipRedirectPatterns = [ENDPOINTS.AUTH.ME, ENDPOINTS.AUTH.REFRESH]
  const shouldSkipRedirect = skipRedirectPatterns.some(p => requestUrl.includes(p))

  if (window.location.pathname !== '/login' && !shouldSkipRedirect) {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.USER)
    window.dispatchEvent(new Event('auth-force-logout'))
    sessionStorage.setItem('redirectAfterLogin', window.location.pathname)
    window.location.href = '/login?expired=true'
  }
}

/**
 * Proactive token refresh on tab focus — when the user returns after
 * being idle, silently refresh if the token expires within 10 minutes.
 * No polling, no multi-tab race (only the visible tab fires).
 */
document.addEventListener('visibilitychange', async () => {
  if (document.visibilityState !== 'visible') return
  const tok = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
  if (!tok) return
  try {
    const payload = JSON.parse(atob(tok.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    if (typeof payload.exp !== 'number') return
    const secsLeft = payload.exp - Math.floor(Date.now() / 1000)
    if (secsLeft > 600 || secsLeft < -60) return
    const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)
    if (!refreshToken) return
    const { data } = await client.post(ENDPOINTS.AUTH.REFRESH, { refresh_token: refreshToken })
    const newAccess = data.accessToken || data.access_token
    const newRefresh = data.refreshToken || data.refresh_token
    if (data.ok && newAccess) {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, newAccess)
      if (newRefresh) localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, newRefresh)
    }
  } catch { /* 401 interceptor handles if refresh also fails */ }
})

/**
 * Response interceptor - Case conversion and unified error handling
 */
client.interceptors.response.use(
  async (response) => {
    await trackResponsePerformance(response)

    // Decrypt response if it was encrypted
    if (response.data?._e && response.config?._aesKey) {
      try {
        response.data = await decryptResponse(response.data, response.config._aesKey)
      } catch {
        // Decryption failed — use as-is
      }
    }

    // Convert response data from snake_case to camelCase (from backend)
    if (response.data && typeof response.data === 'object') {
      response.data = convertKeysToCamel(response.data)
    }
    return response
  },
  async (error) => {
    // Track request duration
    if (error.config?._startTime) {
      error.config._duration = Date.now() - error.config._startTime
    }

    // Decrypt error response if encrypted
    if (error.response?.data?._e && error.config?._aesKey) {
      try {
        error.response.data = await decryptResponse(error.response.data, error.config._aesKey)
      } catch {
        // Decryption failed — use as-is
      }
    }

    // Enrich error with user-friendly properties
    enrichError(error)

    // Track API error and dispatch business error events
    if (!isTelemetryRequest(error.config?.url)) {
      try {
        const { telemetry } = await getTelemetry()
        telemetry.trackApiError(error.config, error, error.response)

        const trackUX = await getTrackUX()
        const handled = dispatchBusinessErrors(error, trackUX)
        if (handled) return Promise.resolve({ data: null, _businessError: true })

        // Network error specific tracking
        if (error.isNetworkError) {
          telemetry.track('ux.network_error', { endpoint: error.config?.url || 'unknown' })
        }
      } catch {
        // Telemetry not available, continue without
      }
    }

    // Handle 401 unauthorized error - attempt token refresh
    const retryResult = await handleUnauthorized(error)
    if (retryResult) return retryResult

    // Log errors in development
    if (import.meta.env.DEV) {
    }

    return Promise.reject(error)
  }
)

/**
 * GET request with automatic retry
 * @param {string} url - API endpoint
 * @param {Object} config - Additional config (can include retry options)
 * @returns {Promise} API response
 */
export async function get(url, config = {}) {
  const { retry, ...axiosConfig } = config
  return withRetry(
    async () => {
      const response = await client.get(url, axiosConfig)
      return response.data
    },
    retry
  )
}

/**
 * POST request with automatic retry
 * @param {string} url - API endpoint
 * @param {Object} data - Request data
 * @param {Object} config - Additional config (can include retry options)
 * @returns {Promise} API response
 */
export async function post(url, data = {}, config = {}) {
  const { retry, ...axiosConfig } = config
  return withRetry(
    async () => {
      const response = await client.post(url, data, axiosConfig)
      return response.data
    },
    retry
  )
}

/**
 * PUT request with automatic retry
 * @param {string} url - API endpoint
 * @param {Object} data - Request data
 * @param {Object} config - Additional config (can include retry options)
 * @returns {Promise} API response
 */
export async function put(url, data = {}, config = {}) {
  const { retry, ...axiosConfig } = config
  return withRetry(
    async () => {
      const response = await client.put(url, data, axiosConfig)
      return response.data
    },
    retry
  )
}

/**
 * PATCH request with automatic retry
 * @param {string} url - API endpoint
 * @param {Object} data - Request data
 * @param {Object} config - Additional config (can include retry options)
 * @returns {Promise} API response
 */
export async function patch(url, data = {}, config = {}) {
  const { retry, ...axiosConfig } = config
  return withRetry(
    async () => {
      const response = await client.patch(url, data, axiosConfig)
      return response.data
    },
    retry
  )
}

/**
 * DELETE request with automatic retry
 * @param {string} url - API endpoint
 * @param {Object} config - Additional config (can include retry options)
 * @returns {Promise} API response
 */
export async function del(url, config = {}) {
  const { retry, ...axiosConfig } = config
  return withRetry(
    async () => {
      const response = await client.delete(url, axiosConfig)
      return response.data
    },
    retry
  )
}

/**
 * Upload file
 * @param {string} url - API endpoint
 * @param {FormData} formData - Form data
 * @param {Function} onUploadProgress - Upload progress callback
 * @returns {Promise} API response
 */
export async function upload(url, formData, onUploadProgress) {
  // Don't manually set Content-Type for FormData - axios will set it with the correct boundary
  const response = await client.post(url, formData, {
    onUploadProgress
  })
  return response.data
}

/**
 * Download file
 * @param {string} url - API endpoint
 * @param {string} filename - Filename
 * @returns {Promise} Blob data
 */
export async function download(url, filename) {
  const response = await client.get(url, {
    responseType: 'blob'
  })

  // Create download link
  const blob = new Blob([response.data])
  const downloadUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(downloadUrl)

  return response.data
}

/**
 * Initialize API client
 * @returns {Promise<void>}
 */
export async function initClient() {
  // Web (cloud) mode: the frontend is served same-origin as the API, relative
  // /api works, and there is no sidecar secret — nothing to do.
  //
  // Desktop (Tauri) mode: the native shell spawns the Python sidecar on a
  // dynamically-resolved 127.0.0.1 port, then navigates the webview to
  //   http://127.0.0.1:{port}/?_secret={secret}
  // This is a full document load, so window.location already points at the live
  // sidecar and relative /api requests reach it. The backend also sets an
  // httponly `_flyto_secret` cookie from the ?_secret= param. We harden two
  // things that otherwise depend on luck:
  //   1. Pin the axios baseURL to the live origin so connectivity is explicit
  //      and never relies on relative-URL resolution.
  //   2. Capture the one-time _secret from the URL and send it as an
  //      X-Flyto2-Secret header on every request — a resilient fallback for the
  //      case where the webview does not retain the auth cookie (otherwise
  //      every API call 403s with no way to recover).
  if (typeof window === 'undefined') return

  const params = new URLSearchParams(window.location.search)
  const secret = params.get('_secret')
  const isDesktop =
    typeof window.__TAURI_INTERNALS__ !== 'undefined' ||
    typeof window.__TAURI__ !== 'undefined' ||
    secret !== null

  if (!isDesktop) return

  if (secret) {
    client.defaults.headers.common['X-Flyto2-Secret'] = secret
  }

  // Only override when no API URL was configured at build time — a configured
  // VITE_API_URL deliberately points the API at a different host.
  if (!import.meta.env.VITE_API_URL && !import.meta.env.VITE_API_BASE_URL) {
    client.defaults.baseURL = `${window.location.origin}/api`
  }
}

// Export axios instance for advanced usage
export { client as axiosInstance }

// Default export
export default {
  get,
  post,
  put,
  patch,
  delete: del,
  upload,
  download,
  client,
  initClient
}
