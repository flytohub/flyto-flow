/**
 * Telemetry Tracker
 *
 * Core event tracking: track, identify, page view, error tracking,
 * interceptor helpers, heartbeat, and global error handlers.
 *
 * All events include trace_id for correlation with backend.
 */

import { post } from '@/api/client'
import { STORAGE_KEYS } from '@/api/config'
import { getDeviceInfo, getPerformanceMetrics } from './device'
import { isCircuitOpen, recordSuccess, recordFailure } from './circuitBreaker'

// =============================================================================
// UUID Generator (lightweight, no external dependency)
// =============================================================================

let fallbackUuidCounter = 0

function generateUUID() {
  const cryptoApi = typeof globalThis !== 'undefined' ? globalThis.crypto : undefined
  if (typeof cryptoApi?.randomUUID === 'function') {
    return cryptoApi.randomUUID()
  }

  if (typeof cryptoApi?.getRandomValues === 'function') {
    const bytes = new Uint8Array(16)
    cryptoApi.getRandomValues(bytes)
    bytes[6] = (bytes[6] & 0x0f) | 0x40
    bytes[8] = (bytes[8] & 0x3f) | 0x80
    const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
  }

  // This last-resort ID is only a correlation key, never an authorization
  // token. Keep it deterministic when Web Crypto is unavailable.
  fallbackUuidCounter += 1
  return `fallback-${Date.now().toString(36)}-${fallbackUuidCounter.toString(36)}`
}

function secureSampleValue() {
  const cryptoApi = typeof globalThis !== 'undefined' ? globalThis.crypto : undefined
  if (typeof cryptoApi?.getRandomValues === 'function') {
    const value = new Uint32Array(1)
    cryptoApi.getRandomValues(value)
    return value[0] / 0x100000000
  }
  fallbackUuidCounter += 1
  return (fallbackUuidCounter % 1000) / 1000
}

// =============================================================================
// Telemetry State
// =============================================================================

// Session ID - persists for browser session
const SESSION_ID = generateUUID()

// Current trace ID - can be set/reset per operation
let currentTraceId = generateUUID()

// Request counter for generating request IDs
let requestCounter = 0

// Event queue for batching (optional future optimization)
const eventQueue = []

// Configuration
const CONFIG = {
  enabled: true,
  endpoint: '/telemetry', // Note: post() already adds /api prefix
  sampleRate: 1.0, // 1.0 = 100% of events
  maxQueueSize: 50,
  flushInterval: 5000 // ms
}

// =============================================================================
// Core Telemetry Object
// =============================================================================

export const telemetry = {
  // ---------------------------------------------------------------------------
  // ID Management
  // ---------------------------------------------------------------------------

  /**
   * Get current trace ID
   * @returns {string} Current trace ID
   */
  getTraceId() {
    return currentTraceId
  },

  /**
   * Set trace ID (for correlation with backend)
   * @param {string} id - Trace ID from backend
   */
  setTraceId(id) {
    currentTraceId = id
  },

  /**
   * Generate new trace ID
   * @returns {string} New trace ID
   */
  resetTraceId() {
    currentTraceId = generateUUID()
    return currentTraceId
  },

  /**
   * Get session ID
   * @returns {string} Session ID (constant per browser session)
   */
  getSessionId() {
    return SESSION_ID
  },

  /**
   * Generate request ID
   * @returns {string} Unique request ID
   */
  generateRequestId() {
    requestCounter++
    return `${SESSION_ID.slice(0, 8)}-${requestCounter}`
  },

  // ---------------------------------------------------------------------------
  // Error Tracking
  // ---------------------------------------------------------------------------

  /**
   * Track a generic error
   * @param {Error} error - Error object
   * @param {Object} context - Additional context
   * @returns {Promise<void>}
   */
  async trackError(error, context = {}) {
    const event = {
      event_type: 'frontend_error',
      event_name: context.name || 'unknown_error',
      trace_id: this.getTraceId(),
      session_id: SESSION_ID,
      error: {
        message: error.message || String(error),
        stack: error.stack || null,
        type: error.name || 'Error'
      },
      properties: context
    }

    return this._send(event)
  },

  /**
   * Track Vue component error
   * @param {Error} error - Error object
   * @param {Object} instance - Vue component instance
   * @param {string} info - Vue lifecycle info
   * @returns {Promise<void>}
   */
  async trackVueError(error, instance, info) {
    return this.trackError(error, {
      name: 'vue.error',
      component: instance?.$options?.name || 'unknown',
      lifecycle: info
    })
  },

  /**
   * Track API error
   * @param {Object} config - Axios request config
   * @param {Error} error - Error object
   * @param {Object} response - Axios response (if any)
   * @returns {Promise<void>}
   */
  async trackApiError(config, error, response) {
    // Skip telemetry endpoint to prevent infinite loop
    if (config?.url?.includes('/telemetry')) {
      return
    }

    const event = {
      event_type: 'frontend_error',
      event_name: 'api.error',
      trace_id: this.getTraceId(),
      session_id: SESSION_ID,
      error: {
        message: error.userMessage || error.message || 'Request failed',
        type: 'ApiError',
        code: String(response?.status || error.code || 'UNKNOWN')
      },
      request: {
        method: config?.method?.toUpperCase(),
        url: this._sanitizeUrl(config?.url),
        status: response?.status,
        duration_ms: config?._duration
      }
    }

    return this._send(event)
  },

  /**
   * Track unhandled promise rejection
   * @param {PromiseRejectionEvent} event - Rejection event
   * @returns {Promise<void>}
   */
  async trackUnhandledRejection(event) {
    const reason = event.reason
    return this.trackError(
      reason instanceof Error ? reason : new Error(String(reason)),
      { name: 'unhandled_rejection' }
    )
  },

  // ---------------------------------------------------------------------------
  // Business Tracking
  // ---------------------------------------------------------------------------

  /**
   * Track a business event
   * @param {string} eventName - Event name (e.g., 'workflow.execute')
   * @param {Object} properties - Event properties
   * @returns {Promise<void>}
   */
  async track(eventName, properties = {}) {
    const event = {
      event_type: 'track_event',
      event_name: eventName,
      trace_id: this.getTraceId(),
      session_id: SESSION_ID,
      properties
    }

    return this._send(event)
  },

  /**
   * Track page view
   * @param {string} path - Page path
   * @param {Object} properties - Additional properties
   * @returns {Promise<void>}
   */
  async trackPageView(path, properties = {}) {
    // Get performance metrics (only meaningful on initial page load)
    const perf = getPerformanceMetrics()

    return this.track('page.view', {
      path,
      referrer: document.referrer,
      title: document.title,
      ...(perf && { performance: perf }),
      ...properties
    })
  },

  /**
   * Track button click
   * @param {string} buttonId - Button identifier
   * @param {Object} properties - Additional properties
   * @returns {Promise<void>}
   */
  async trackClick(buttonId, properties = {}) {
    return this.track('button.click', {
      buttonId,
      ...properties
    })
  },

  // ---------------------------------------------------------------------------
  // Configuration
  // ---------------------------------------------------------------------------

  /**
   * Enable/disable telemetry
   * @param {boolean} enabled - Enable flag
   */
  setEnabled(enabled) {
    CONFIG.enabled = enabled
  },

  /**
   * Set sample rate
   * @param {number} rate - Sample rate (0.0 to 1.0)
   */
  setSampleRate(rate) {
    CONFIG.sampleRate = Math.max(0, Math.min(1, rate))
  },

  // ---------------------------------------------------------------------------
  // Internal Methods
  // ---------------------------------------------------------------------------

  /**
   * Send event to backend
   * @param {Object} event - Event data
   * @returns {Promise<void>}
   */
  async _send(event) {
    // Check if enabled
    if (!CONFIG.enabled) {
      return
    }
    if (isCircuitOpen()) {
      return
    }

    // Apply sampling
    if (secureSampleValue() > CONFIG.sampleRate) {
      return
    }

    // Add common fields
    event.timestamp = new Date().toISOString()
    event.environment = import.meta.env.MODE || 'development'
    event.version = import.meta.env.VITE_APP_VERSION || '1.0.0'
    event.source = 'frontend'

    // Add device info
    event.device = getDeviceInfo()

    // Add user info (note: backend will also add from auth token)
    const userStr = localStorage.getItem(STORAGE_KEYS.USER)
    if (userStr) {
      try {
        const user = JSON.parse(userStr)
        event.user_id = user.id || user.uid
        event.user_email = user.email
      } catch {
        // Ignore parse errors
      }
    }

    // Send to backend
    try {
      await post(CONFIG.endpoint, event)
      recordSuccess()
    } catch (err) {
      // Telemetry failure should never affect user experience
      recordFailure()
      if (import.meta.env.DEV) {
      }
    }
  },

  /**
   * Sanitize URL by removing sensitive query params
   * @param {string} url - URL to sanitize
   * @returns {string} Sanitized URL
   */
  _sanitizeUrl(url) {
    if (!url) return url

    try {
      const parsed = new URL(url, window.location.origin)
      const sensitiveParams = ['token', 'key', 'secret', 'password', 'api_key']
      sensitiveParams.forEach((param) => {
        if (parsed.searchParams.has(param)) {
          parsed.searchParams.set(param, '[REDACTED]')
        }
      })
      return parsed.pathname + parsed.search
    } catch {
      return url
    }
  }
}

// =============================================================================
// Global Error Handlers Setup
// =============================================================================

/**
 * Initialize global error handlers
 * Call this in main.js after Vue app is created
 */
export function initTelemetryErrorHandlers() {
  // Unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    telemetry.trackUnhandledRejection(event)
  })

  // Global errors (rare, mostly caught by Vue)
  window.addEventListener('error', (event) => {
    telemetry.trackError(event.error || new Error(event.message), {
      name: 'global.error',
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    })
  })
}

// =============================================================================
// Axios Interceptor Helpers
// =============================================================================

/**
 * Add telemetry headers to request config
 * @param {Object} config - Axios request config
 * @returns {Object} Modified config
 */
export function addTelemetryHeaders(config) {
  config.headers = config.headers || {}
  config.headers['X-Trace-ID'] = telemetry.getTraceId()
  config.headers['X-Session-ID'] = telemetry.getSessionId()
  config._startTime = Date.now()
  return config
}

/**
 * Track request duration in response
 * @param {Object} response - Axios response
 * @returns {Object} Response with duration
 */
export function trackRequestDuration(response) {
  if (response.config?._startTime) {
    response.config._duration = Date.now() - response.config._startTime
  }
  return response
}

/**
 * Track API error in interceptor
 * @param {Error} error - Axios error
 * @returns {Promise<Error>} Rejected error
 */
export function trackApiErrorInterceptor(error) {
  const config = error.config || {}
  if (config._startTime) {
    config._duration = Date.now() - config._startTime
  }

  telemetry.trackApiError(config, error, error.response)

  return Promise.reject(error)
}

// =============================================================================
// Heartbeat / Presence Tracking
// =============================================================================

let heartbeatInterval = null
let isHeartbeatRunning = false

/**
 * Start heartbeat for presence tracking
 * Sends periodic updates to mark user as online
 */
export function startHeartbeat() {
  if (isHeartbeatRunning) return

  isHeartbeatRunning = true

  // Send initial heartbeat
  sendHeartbeat()

  // Send heartbeat every 30 seconds
  heartbeatInterval = setInterval(sendHeartbeat, 30000)

  // Also send heartbeat on visibility change (when tab becomes visible)
  document.addEventListener('visibilitychange', handleVisibilityChange)

  // Send heartbeat on page unload to capture last page
  window.addEventListener('beforeunload', sendHeartbeat)
}

/**
 * Stop heartbeat
 */
export function stopHeartbeat() {
  isHeartbeatRunning = false

  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
    heartbeatInterval = null
  }

  document.removeEventListener('visibilitychange', handleVisibilityChange)
  window.removeEventListener('beforeunload', sendHeartbeat)
}

/**
 * Handle visibility change - send heartbeat when tab becomes visible
 */
function handleVisibilityChange() {
  if (document.visibilityState === 'visible') {
    sendHeartbeat()
  }
}

/**
 * Send heartbeat to server
 */
async function sendHeartbeat() {
  if (!CONFIG.enabled) return
  if (isCircuitOpen()) return
  try {
    const result = await post('/telemetry/heartbeat', {
      session_id: SESSION_ID,
      page: window.location.pathname,
      device: getDeviceInfo()
    })

    if (!result?.ok && result?.status !== 'anonymous') {
      console.error('[Heartbeat] Failed:', result?.error)
    }
  } catch (err) {
    console.error('[Heartbeat] Error:', err.message)
  }
}

// =============================================================================
// Default Export
// =============================================================================

export default telemetry
