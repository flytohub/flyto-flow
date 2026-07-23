/**
 * CE API configuration.
 *
 * CE only talks to the backend that served the UI, or to an explicitly
 * configured loopback address during local development.
 */
import { DEFAULTS, getWebSocketUrl } from './defaults'

const getApiBaseUrl = () => {
  if (import.meta.env.DEV) return ''
  return import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || ''
}

const apiBaseUrl = getApiBaseUrl()

export const API_BASE_URL = apiBaseUrl
export const API_URL = apiBaseUrl ? `${apiBaseUrl}/api` : '/api'
export const WS_BASE_URL = getWebSocketUrl(apiBaseUrl)
export const REQUEST_TIMEOUT = DEFAULTS.API.TIMEOUT
export const RETRY_CONFIG = {
  maxRetries: DEFAULTS.RETRY.MAX_RETRIES,
  retryDelay: DEFAULTS.RETRY.DELAY,
  retryableStatuses: DEFAULTS.RETRY.RETRYABLE_STATUSES
}

export async function initApiUrl() {
  return apiBaseUrl
}

export function getApiUrl() {
  return API_URL
}

export function getWsUrl() {
  return getWebSocketUrl(apiBaseUrl)
}

export const ENDPOINTS = {
  CONFIG: {
    PLATFORM: '/config/platform',
    CONSTANTS: '/config/constants',
    CATEGORIES: '/config/categories',
    CATEGORIES_VISIBLE: '/config/categories/visible',
    FEATURE_FLAGS: '/config/feature-flags'
  },
  WORKFLOWS: {
    RUN: '/workflows/run'
  },
  EXECUTIONS: {
    GET: (id) => `/executions/${id}`,
    WS: (id) => `/ws/executions/${id}`,
    PAUSE: (id) => `/executions/${id}/pause`,
    RESUME: (id) => `/executions/${id}/resume`,
    STEP: (id) => `/executions/${id}/step`,
    STATE: (id) => `/executions/${id}/state`,
    RUN_TO_END: (id) => `/executions/${id}/run-to-end`,
    RESUME_OPTIONS: (id) => `/executions/${id}/resume-options`,
    RESUME_CHECKPOINT: (id) => `/executions/${id}/resume-from-checkpoint`,
    CONTINUE_CHECKPOINT: (id) => `/executions/${id}/continue-checkpoint`,
    BYPASS_CHECKPOINT: (id) => `/executions/${id}/bypass-checkpoint`,
    BROWSER_WS: (id) => `/ws/browser/${id}`,
    BROWSER_STATUS: (id) => `/browser/${id}/screencast/status`
  },
  MODULES: {
    CATALOG: '/modules/catalog',
    TIERED: '/modules/tiered',
    GET: (id) => `/modules/${id}`
  },
  METRICS: {
    SUMMARY: '/metrics/summary',
    TREND: '/metrics/trend',
    TOP_WORKFLOWS: '/metrics/top-workflows',
    RECENT_FAILURES: '/metrics/recent-failures',
    EXPORT: '/metrics/export'
  },
  TRACES: {
    LIST: '/traces',
    GET: (traceId) => `/traces/${traceId}`,
    SPANS: (traceId) => `/traces/${traceId}/spans`,
    SEARCH: '/traces/search'
  },
  ALERTS: {
    LIST: '/alerts',
    GET: (id) => `/alerts/${id}`,
    ACKNOWLEDGE: (id) => `/alerts/${id}/acknowledge`,
    MUTE: (id) => `/alerts/${id}/mute`,
    RULES: '/alerts/rules',
    RULE: (id) => `/alerts/rules/${id}`,
    HISTORY: '/alerts/history'
  },
  DEBUG: {
    TIMELINE: (executionId) => `/debug/timeline/${executionId}`,
    NODE_DETAIL: (executionId, nodeId) => `/debug/timeline/${executionId}/node/${nodeId}`,
    RERUN: (executionId) => `/debug/rerun/${executionId}`,
    HISTORY: (workflowId) => `/debug/history/${workflowId}`,
    STATS: (workflowId) => `/debug/stats/${workflowId}`
  },
  VARIABLES: {
    LIST: '/variables',
    CREATE: '/variables',
    GET: (id) => `/variables/${id}`,
    UPDATE: (id) => `/variables/${id}`,
    DELETE: (id) => `/variables/${id}`,
    RESOLVE: (workflowId) => `/variables/resolve/${workflowId}`,
    CREDENTIALS: '/variables/credentials',
    CREDENTIAL: (id) => `/variables/credentials/${id}`,
    CREDENTIAL_REVEAL: (id) => `/variables/credentials/${id}/reveal`,
    CREDENTIAL_AUDIT: '/variables/credentials/audit'
  },
}

export const STORAGE_KEYS = {
  LANGUAGE: 'language',
  THEME: 'theme'
}
