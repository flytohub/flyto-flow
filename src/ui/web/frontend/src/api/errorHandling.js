/**
 * API Error Handling Utilities
 *
 * Extracted from client.js for clarity and testability.
 * Handles error message mapping, retry logic, and error event dispatching.
 */

/**
 * Error code to message mapping
 */
const ERROR_MESSAGES = {
  400: 'errors.badRequest',
  401: 'errors.unauthorized',
  403: 'errors.forbidden',
  404: 'errors.notFound',
  408: 'errors.timeout',
  409: 'errors.conflict',
  422: 'errors.validationFailed',
  429: 'errors.tooManyRequests',
  500: 'errors.serverError',
  502: 'errors.badGateway',
  503: 'errors.serviceUnavailable',
  504: 'errors.gatewayTimeout'
}

const DEFAULT_MESSAGES = {
  400: 'Invalid request. Please check your input.',
  401: 'Please log in to continue.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested resource was not found.',
  408: 'Request timed out. Please try again.',
  409: 'This action conflicts with existing data.',
  422: 'Validation failed. Please check your input.',
  429: 'Too many requests. Please wait a moment.',
  500: 'Server error. Please try again later.',
  502: 'Service temporarily unavailable.',
  503: 'Service is under maintenance. Please try again later.',
  504: 'Server took too long to respond.'
}

/**
 * Get user-friendly error message
 * @param {Error} error - Axios error
 * @returns {{ key: string|null, fallback: string }}
 */
export function getErrorMessage(error) {
  if (!error.response) {
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      return { key: 'errors.timeout', fallback: 'Request timed out. Please try again.' }
    }
    if (error.code === 'ERR_NETWORK' || error.message?.includes('Network') || error.message?.includes('network')) {
      return { key: 'errors.networkError', fallback: 'Unable to connect to server. Please ensure the backend is running.' }
    }
    if (error.message?.includes('CORS') || error.message?.includes('cross-origin')) {
      return { key: 'errors.corsError', fallback: 'Connection blocked by browser security. Please check CORS configuration.' }
    }
    return { key: 'errors.unknownError', fallback: 'An unexpected error occurred.' }
  }

  const status = error.response.status
  // Backend uses {ok, error, error_code} format (from errors.py exception handler)
  const serverMessage = error.response.data?.error || error.response.data?.detail || error.response.data?.message

  if (serverMessage) {
    return { key: null, fallback: serverMessage }
  }

  const messageKey = ERROR_MESSAGES[status]
  if (messageKey) {
    return { key: messageKey, fallback: DEFAULT_MESSAGES[status] || 'An unexpected error occurred.' }
  }

  return { key: 'errors.unknownError', fallback: 'An unexpected error occurred.' }
}

/**
 * Enrich error object with user-friendly properties
 * @param {Error} error - Axios error
 */
export function enrichError(error) {
  const errorInfo = getErrorMessage(error)
  error.userMessage = errorInfo.fallback
  error.messageKey = errorInfo.key
  error.status = error.response?.status
  error.isNetworkError = !error.response
  error.isTimeout = error.code === 'ECONNABORTED'
  error.isRetryable = [408, 429, 500, 502, 503, 504].includes(error.status) || error.isNetworkError
}

/**
 * Dispatch business error events (trial expired, insufficient credits, etc.)
 * @param {Error} error - Axios error (already enriched)
 * @param {Function} trackUX - UX tracking function
 */
export function dispatchBusinessErrors(error, trackUX) {
  const endpoint = error.config?.url || 'unknown'
  const status = error.response?.status
  const data = error.response?.data || {}

  // Backend error handler now puts full dict in `details` field.
  // Also check `detail` (FastAPI default) and top-level for backward compat.
  const info = data.details || data.detail || data
  const errorCode = data.errorCode || data.error_code || info?.errorCode || info?.error_code
  const errorType = info?.error || data?.error

  // --- Payment required (402) → always show UpgradeModal ---
  // All payment/subscription/trial errors are 402. 403 is only for permission.
  if (status === 402) {
    trackUX.permissionDenied(endpoint, errorType || 'payment_required')

    if (errorType === 'trial_expired' || errorCode === 'TRIAL_EXPIRED' || errorCode === 'TRIAL_AND_SUBSCRIPTION_EXPIRED') {
      window.dispatchEvent(new CustomEvent('trial-expired', {
        detail: {
          expiresAt: info?.expiresAt || info?.expires_at || info?.trialExpiresAt || info?.trial_expires_at,
          message: info?.message || data?.error,
        }
      }))
    } else if (errorType === 'insufficient_credits') {
      window.dispatchEvent(new CustomEvent('insufficient-credits', {
        detail: { balance: info?.balance, required: info?.required }
      }))
    } else if (errorType === 'purchase_required') {
      window.dispatchEvent(new CustomEvent('purchase-required', {
        detail: {
          templateId: info?.templateId || info?.template_id,
          templateName: info?.templateName || info?.template_name,
          price: info?.price,
        }
      }))
    } else {
      // Generic 402: feature gate, license required, quota exceeded, etc.
      window.dispatchEvent(new CustomEvent('feature-upgrade-required', {
        detail: {
          feature: info?.feature,
          message: info?.message || errorType || data?.error,
          licenseType: info?.licenseType || info?.license_type,
          reasonCode: info?.reasonCode || info?.reason_code || 'license_required',
        }
      }))
    }
    return true
  }

  // --- Permission denied (403, non-trial) ---
  if (status === 403) {
    trackUX.permissionDenied(endpoint, null)
    return
  }

  // Quota exceeded (429)
  if (status === 429) {
    const detail = error.response?.data?.detail || error.response?.data
    const isQuotaExceeded = detail?.error === 'quota_exceeded'
    trackUX.quotaExceeded(isQuotaExceeded ? detail?.feature : 'api_requests', null)
    if (isQuotaExceeded) {
      window.dispatchEvent(new CustomEvent('feature-quota-exceeded', {
        detail: {
          feature: detail?.feature,
          current: detail?.current,
          limit: detail?.limit,
          unit: detail?.unit,
          message: detail?.message,
        }
      }))
    }
    return
  }

  // Timeout
  if (error.isTimeout) {
    trackUX.timeout(endpoint, error.config?._duration || 0)
    return
  }

  // Network error
  if (error.isNetworkError) {
    // Already tracked via telemetry.trackApiError; no extra dispatch needed
    return
  }

  // Server error (5xx)
  if (status >= 500) {
    trackUX.apiError(endpoint, status, error.userMessage)
  }
}

// =============================================================================
// Retry Logic with Exponential Backoff
// =============================================================================

/**
 * Default retry configuration
 */
const DEFAULT_RETRY_CONFIG = {
  maxRetries: 3,
  baseDelay: 1000,  // 1 second
  maxDelay: 10000,  // 10 seconds
  retryableStatuses: [408, 429, 500, 502, 503, 504]
}

/**
 * Sleep for a given number of milliseconds
 * @param {number} ms
 * @returns {Promise<void>}
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Calculate delay with exponential backoff and jitter
 * @param {number} attempt - Current attempt number (0-based)
 * @param {number} baseDelay - Base delay in ms
 * @param {number} maxDelay - Maximum delay in ms
 * @returns {number} Delay in ms
 */
function calculateBackoff(attempt, baseDelay, maxDelay) {
  const exponentialDelay = baseDelay * Math.pow(2, attempt)
  const jitter = exponentialDelay * Math.random() * 0.25
  return Math.min(exponentialDelay + jitter, maxDelay)
}

/**
 * Check if an error is retryable
 * @param {Error} error - The error to check
 * @param {number[]} retryableStatuses - List of retryable HTTP status codes
 * @returns {boolean}
 */
function isRetryableError(error, retryableStatuses) {
  if (!error.response) {
    return error.code === 'ECONNABORTED' ||
           error.code === 'ERR_NETWORK' ||
           error.message?.includes('timeout') ||
           error.message?.includes('Network')
  }
  return retryableStatuses.includes(error.response.status)
}

/**
 * Execute a request function with retry logic
 * @param {Function} requestFn - Async function that makes the request
 * @param {Object} config - Retry configuration
 * @returns {Promise<any>} Request result
 */
export async function withRetry(requestFn, config = {}) {
  const {
    maxRetries = DEFAULT_RETRY_CONFIG.maxRetries,
    baseDelay = DEFAULT_RETRY_CONFIG.baseDelay,
    maxDelay = DEFAULT_RETRY_CONFIG.maxDelay,
    retryableStatuses = DEFAULT_RETRY_CONFIG.retryableStatuses
  } = config

  let lastError

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error

      if (!isRetryableError(error, retryableStatuses) || attempt === maxRetries) {
        throw error
      }

      const delay = calculateBackoff(attempt, baseDelay, maxDelay)
      await sleep(delay)
    }
  }

  throw lastError
}
