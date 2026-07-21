/**
 * API Configuration
 * Single source of truth for all API settings
 */

import { DEFAULTS, getDefaultApiUrl, getWebSocketUrl } from './defaults'

/**
 * Get API base URL
 */
const getApiBaseUrl = () => {
  // In development, use relative URL to leverage Vite's proxy
  if (import.meta.env.DEV) {
    return ''
  }

  // In production, use configured URL or relative path (same origin)
  // Empty string = relative URLs, which works when frontend is served by the same server
  return (
    import.meta.env.VITE_API_URL ||
    import.meta.env.VITE_API_BASE_URL ||
    ''
  )
}

// Resolved once at module load — immutable after initialization.
const _apiBaseUrl = getApiBaseUrl()

export const API_BASE_URL = _apiBaseUrl
export const API_URL = _apiBaseUrl ? `${_apiBaseUrl}/api` : '/api'
export const WS_BASE_URL = getWebSocketUrl(_apiBaseUrl)

/**
 * Initialize API URL
 * @returns {Promise<string>} The resolved API base URL
 */
export async function initApiUrl() {
  return _apiBaseUrl
}

/**
 * Get current API base URL (for dynamic use)
 * @returns {string}
 */
export function getApiUrl() {
  return _apiBaseUrl ? `${_apiBaseUrl}/api` : '/api'
}

/**
 * Get current WebSocket base URL (for dynamic use)
 * @returns {string}
 */
export function getWsUrl() {
  return getWebSocketUrl(_apiBaseUrl)
}
export const REQUEST_TIMEOUT = DEFAULTS.API.TIMEOUT

export const RETRY_CONFIG = {
  maxRetries: DEFAULTS.RETRY.MAX_RETRIES,
  retryDelay: DEFAULTS.RETRY.DELAY,
  retryableStatuses: DEFAULTS.RETRY.RETRYABLE_STATUSES
}

const AUTH_PATHS = {
  CHANGE: '/auth/change-password',
  FORGOT: '/auth/forgot-password',
  RESET: '/auth/reset-password',
  VERIFY_RESET_CODE: '/auth/verify-reset-code',
}

export const ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    ME: '/auth/me',
    CHANGE_PASSWORD: AUTH_PATHS.CHANGE,
    FORGOT_PASSWORD: AUTH_PATHS.FORGOT,
    RESET_PASSWORD: AUTH_PATHS.RESET,
    VERIFY_RESET_CODE: AUTH_PATHS.VERIFY_RESET_CODE,
    REFRESH: '/auth/refresh',
    CONFIG: '/auth/config',
    GOOGLE_LOGIN: '/auth/google-login',
    GITHUB_LOGIN: '/auth/github-login',
    LINKED_PROVIDERS: '/auth/linked-providers',
    LINK_GOOGLE: '/auth/link-google',
    LINK_GITHUB: '/auth/link-github',
    UNLINK_PROVIDER: '/auth/unlink-provider'
  },

  CONFIG: {
    PLATFORM: '/config/platform',
    CONSTANTS: '/config/constants',
    CATEGORIES: '/config/categories',
    CATEGORIES_VISIBLE: '/config/categories/visible',
    FEATURE_FLAGS: '/config/feature-flags'
  },

  LICENSES: {
    LIST: '/licenses',
    STATUS: '/licenses/status',
    GET: (id) => `/licenses/${id}`,
    DOWNLOAD: (id) => `/licenses/${id}/download`,
    DEVICES: (id) => `/licenses/${id}/devices`,
    TRANSFER: (id) => `/licenses/${id}/transfer`,
    REMOVE_DEVICE: (id) => `/licenses/${id}/devices`
  },

  DASHBOARD: {
    STATS: '/dashboard/stats',
    SALES_TREND: '/dashboard/sales-trend',
    RECENT_TEMPLATES: '/dashboard/recent-templates',
    RECENT_ACTIVITY: '/dashboard/recent-activity'
  },

  TEMPLATES: {
    LIST: '/templates/',
    GET: (id) => `/templates/${id}`,
    CREATE: '/templates/',
    UPDATE: (id) => `/templates/${id}`,
    DELETE: (id) => `/templates/${id}`,
    EXECUTE: (id) => `/templates/${id}/execute`,
    SEARCH: '/templates/search',
    CATEGORIES: '/templates/categories',
    AVAILABLE_TAGS: '/templates/available-tags',
    // Library
    LIBRARY: '/templates/library',
    LIBRARY_ADD: (id) => `/templates/library/${id}`,
    LIBRARY_REMOVE: (id) => `/templates/library/${id}`,
    // Reviews
    REVIEWS: (id) => `/templates/${id}/reviews`,
    REVIEW_CREATE: (id) => `/templates/${id}/reviews`,
    // YAML
    EXPORT: (id) => `/templates/${id}/export`,
    IMPORT_YAML: '/templates/import/yaml',
    PUSH_YAML: (id) => `/templates/${id}/push`,
  },

  WORKFLOWS: {
    LIST: '/workflows',
    GET: (id) => `/workflows/${id}`,
    CREATE: '/workflows',
    UPDATE: (id) => `/workflows/${id}`,
    DELETE: (id) => `/workflows/${id}`,
    EXECUTE: (id) => `/workflows/${id}/execute`,
    RUN: '/workflows/run',
    EXECUTIONS: (id) => `/workflows/${id}/executions`,
    HISTORY: (id) => `/workflows/${id}/history`,
    MODULES: '/workflows/modules'
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
    // Human Checkpoint
    CONTINUE_CHECKPOINT: (id) => `/executions/${id}/continue-checkpoint`,
    BYPASS_CHECKPOINT: (id) => `/executions/${id}/bypass-checkpoint`,
    // Browser Screencast
    BROWSER_WS: (id) => `/ws/browser/${id}`,
    BROWSER_STATUS: (id) => `/browser/${id}/screencast/status`
  },

  // NOTE: admin endpoints were moved to the flyto-admin app/BFF.
  // The former ENDPOINTS.ADMIN block (users/config/orders/licenses/…) was dead
  // code here — zero references in this frontend — and has been removed. Any
  // admin functionality now lives in the flyto-admin repo.

  TRANSLATIONS: {
    FILES: '/admin/translations/files',
    FILE: (locale, filename) => `/admin/translations/files/${locale}/${filename}`,
    SAVE: (locale, filename) => `/admin/translations/files/${locale}/${filename}`,
    STATS: '/admin/translations/stats',
    // GitHub
    GITHUB_PR: '/admin/translations/github/pr',
    GITHUB_PR_STATUS: (number) => `/admin/translations/github/pr/${number}`,
    GITHUB_PRS: '/admin/translations/github/prs',
    // Import/Export
    IMPORT: '/admin/translations/import',
    EXPORT: (locale) => `/admin/translations/export/${locale}`,
    // AI
    AI_TRANSLATE: '/admin/translations/ai/translate'
  },

  MODULES: {
    CATALOG: '/modules/catalog',
    TIERED: '/modules/tiered',
    GET: (id) => `/modules/${id}`
  },

  AI: {
    CHAT: '/ai/chat',
    SUGGESTIONS: '/ai/suggestions',
    HEALTH: '/ai/health',
    CONFIG: '/ai/config',
    CONFIG_TEST: '/ai/config/test'
  },

  // Security (Step gate validation - authoritative server-side)
  SECURITY: {
    STEP_GATE_CONFIG: '/security/step-gate-config',
    VALIDATE_STEP: '/security/validate-step',
    VALIDATE_SHELL: '/security/validate-shell-command'
  },

  CHAT: {
    CONVERSATIONS: '/chat/conversations',
    CONVERSATION: (id) => `/chat/conversations/${id}`,
    MESSAGES: '/chat/messages',
    MARK_READ: (id) => `/chat/conversations/${id}/read`,
    UPLOAD: '/chat/upload'
  },

  USERS: {
    PROFILE: '/users/profile',
    AVATAR: '/users/avatar',
    GET: (id) => `/users/${id}`,
    FOLLOW: (id) => `/users/${id}/follow`,
    FOLLOW_STATUS: (id) => `/users/follow/${id}/status`,
    FOLLOWERS: '/users/followers',
    FOLLOWERS_USER: (id) => `/users/${id}/followers`,
    FOLLOWING: '/users/following',
    FOLLOWING_USER: (id) => `/users/${id}/following`
  },

  NOTIFICATIONS: {
    LIST: '/notifications',
    GET: (id) => `/notifications/${id}`,
    MARK_READ: (id) => `/notifications/${id}/read`,
    MARK_ALL_READ: '/notifications/read-all',
    UNREAD_COUNT: '/notifications/unread-count'
  },

  STORAGE: {
    UPLOAD: '/storage/upload',
    LIST: '/storage',
    DELETE: (id) => `/storage/${id}`
  },

  ORDERS: {
    LIST: '/orders',
    GET: (id) => `/orders/${id}`,
    CREATE: '/orders',
    RESPOND: (id) => `/orders/${id}/respond`,
    START: (id) => `/orders/${id}/start`,
    DELIVER: (id) => `/orders/${id}/deliver`,
    COMPLETE: (id) => `/orders/${id}/complete`,
    CANCEL: (id) => `/orders/${id}/cancel`
  },

  PAYMENT: {
    CHECKOUT: '/payment/checkout',
    CONNECT_STATUS: '/payment/connect/status',
    CONNECT_BALANCE: '/payment/connect/balance',
    CONNECT_ONBOARD: '/payment/connect/onboard',
    EARNINGS: '/payment/earnings',
    SALES: '/payment/sales',
    PAYOUTS: '/payment/payouts',
    PAYOUT_REQUEST: '/payment/payout',
    VERIFY_PURCHASE: (templateId) => `/payment/purchases/${templateId}/verify`,
    // Purchase history & refund
    PURCHASES: '/payment/purchases',
    REFUND_ELIGIBILITY: (purchaseId) => `/payment/purchases/${purchaseId}/refund-eligibility`,
    REFUND: (purchaseId) => `/payment/purchases/${purchaseId}/refund`
  },

  INVITE_KEYS: {
    LIST: '/invite-keys',
    GET: (id) => `/invite-keys/${id}`,
    CREATE: '/invite-keys',
    BATCH_CREATE: '/invite-keys/batch',
    STATS: '/invite-keys/stats',
    VALIDATE: (key) => `/invite-keys/validate/${key}`,
    USE: '/invite-keys/use',
    REVOKE: (id) => `/invite-keys/${id}/revoke`
  },

  WALLET: {
    BALANCE: '/wallet/balance',
    TRANSACTIONS: '/wallet/transactions',
    PACKAGES: '/wallet/packages',
    TOPUP: '/wallet/topup'
  },

  SUBSCRIPTIONS: {
    ME: '/subscriptions/me',
    // Real Stripe Checkout flow — entitlement granted only by the Stripe webhook
    // after a verified payment. This is the customer-facing upgrade path.
    SUBSCRIBE: '/subscriptions/subscribe',
    // Admin/system only: records a subscription directly (no payment). 403 for users.
    CREATE: '/subscriptions',
    CANCEL: '/subscriptions/cancel',
    // Admin endpoints
    LIST: '/subscriptions',
    GET: (id) => `/subscriptions/${id}`,
    GRANT: '/subscriptions/grant',
    STATS: '/subscriptions/stats'
  },

  API_KEYS: {
    LIST: '/api-keys',
    CREATE: '/api-keys',
    GET: (id) => `/api-keys/${id}`,
    REVOKE: (id) => `/api-keys/${id}/revoke`,
    DELETE: (id) => `/api-keys/${id}`
  },

  REPORTS: {
    CREATE: '/reports',
    MY_REPORTS: '/reports/my-reports',
    LIST: '/reports',
    GET: (id) => `/reports/${id}`,
    UPDATE: (id) => `/reports/${id}`,
    DELETE: (id) => `/reports/${id}`,
    STATS: '/reports/stats'
  },

  ISSUES: {
    LIST: '/issues/',
    GET: (id) => `/issues/${id}`,
    CREATE: '/issues/',
    UPDATE: (id) => `/issues/${id}`,
    DELETE: (id) => `/issues/${id}`,
    UPVOTE: (id) => `/issues/${id}/upvote`,
    COMMENTS: (id) => `/issues/${id}/comments`,
    DELETE_COMMENT: (id, cid) => `/issues/${id}/comments/${cid}`,
  },

  USER_TOOLS: {
    LIST: '/user-tools',
    PUBLIC: '/user-tools/public',
    GET: (id) => `/user-tools/${id}`,
    CREATE: '/user-tools',
    UPDATE: (id) => `/user-tools/${id}`,
    DELETE: (id) => `/user-tools/${id}`,
    EXECUTE: (id) => `/user-tools/${id}/execute`
  },

  // Phase 8: Observability
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

  // Phase 9: Version Control & Audit
  VERSIONS: {
    LIST: (workflowId) => `/workflows/${workflowId}/versions`,
    GET: (workflowId, version) => `/workflows/${workflowId}/versions/${version}`,
    DIFF: (workflowId) => `/workflows/${workflowId}/versions/diff`,
    ROLLBACK: (workflowId, version) => `/workflows/${workflowId}/versions/${version}/rollback`
  },

  AUDIT: {
    LIST: '/audit',
    GET: (id) => `/audit/${id}`,
    VERIFY: '/audit/verify',
    EXPORT: '/audit/export',
    STATS: '/audit/stats'
  },

  // Phase 3: Debug System
  DEBUG: {
    TIMELINE: (execId) => `/debug/timeline/${execId}`,
    NODE_DETAIL: (execId, nodeId) => `/debug/timeline/${execId}/node/${nodeId}`,
    VARIABLES: (execId) => `/debug/timeline/${execId}/variables`,
    REPLAY: (execId) => `/debug/replay/${execId}`,
    RERUN: (execId) => `/debug/rerun/${execId}`,
    COMPARE: '/debug/compare',
    ERROR_ANALYSIS: (execId) => `/debug/error-analysis/${execId}`,
    HISTORY: (workflowId) => `/debug/history/${workflowId}`,
    STATS: (workflowId) => `/debug/stats/${workflowId}`
  },

  // Phase 4: Variable Management
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

  // Phase 6: Triggers
  TRIGGERS: {
    // Schedules
    SCHEDULES: '/triggers/schedules',
    SCHEDULE: (id) => `/triggers/schedules/${id}`,
    SCHEDULE_PAUSE: (id) => `/triggers/schedules/${id}/pause`,
    SCHEDULE_RESUME: (id) => `/triggers/schedules/${id}/resume`,
    SCHEDULE_TRIGGER: (id) => `/triggers/schedules/${id}/trigger`,
    // Webhooks
    WEBHOOKS: '/triggers/webhooks',
    WEBHOOK: (id) => `/triggers/webhooks/${id}`,
    WEBHOOK_REGENERATE: (id) => `/triggers/webhooks/${id}/regenerate-secret`,
    WEBHOOK_DISABLE: (id) => `/triggers/webhooks/${id}/disable`,
    WEBHOOK_ENABLE: (id) => `/triggers/webhooks/${id}/enable`,
    WEBHOOK_TRIGGER: (id) => `/triggers/webhooks/${id}/trigger`,
    WEBHOOK_TEST_START: (id) => `/triggers/webhooks/${id}/test/start`,
    WEBHOOK_TEST_RESULT: (id) => `/triggers/webhooks/${id}/test/result`,
    // Utilities
    CRON_NEXT: '/triggers/cron/next',
    CRON_VALIDATE: '/triggers/cron/validate',
    NONCES_CLEANUP: '/triggers/nonces/cleanup',
  },

  // Devices (Runner Device Management)
  DEVICES: {
    LIST: '/devices',
    REGISTER: '/devices/register',
    GET: (id) => `/devices/${id}`,
    DELETE: (id) => `/devices/${id}`,
    HEARTBEAT: (id) => `/devices/${id}/heartbeat`,
    REVOKE: (id) => `/devices/${id}/revoke`,
    STATS: '/devices/stats',
    EXECUTE: (id) => `/devices/${id}/execute`,
    JOBS: '/devices/jobs',
    JOB_STATE: (id) => `/devices/jobs/${id}/state`,
    JOB_CANCEL: (id) => `/devices/jobs/${id}/cancel`,
    WAKE: (id) => `/devices/${id}/wake`,
    WAKE_POLL: (id) => `/devices/${id}/wake-poll`,
    REMOTE_WAKE_SETTING: (id) => `/devices/${id}/remote-wake-setting`,
    CLOUD_EXECUTE: '/devices/cloud/execute',
  },

  // Telemetry (Error collection, business tracking)
  // Creator Dashboard
  CREATOR: {
    STATS_REGIONAL: '/creator/stats/regional',
    STATS_OVERVIEW: '/creator/stats/overview',
    STATS_TEMPLATES: '/creator/stats/templates'
  },

  // Translation Reviews (User)
  TRANSLATION_REVIEWS: {
    SUBMIT: '/translation-reviews',
    MY: '/translation-reviews/my',
    // Admin endpoints
    LIST: '/translation-reviews',
    GET: (id) => `/translation-reviews/${id}`,
    UPDATE: (id) => `/translation-reviews/${id}`,
    DELETE: (id) => `/translation-reviews/${id}`,
    PENDING_COUNT: '/translation-reviews/pending/count'
  },

  TELEMETRY: {
    TRACK: '/telemetry',
    HEARTBEAT: '/telemetry/heartbeat',
    // Admin endpoints
    ADMIN_LIST: '/admin/telemetry',
    ADMIN_TRACE: (traceId) => `/admin/telemetry/traces/${traceId}`,
    ADMIN_STATS: '/admin/telemetry/stats',
    // Analytics endpoints
    ADMIN_OVERVIEW: '/admin/telemetry/overview',
    ADMIN_USERS: '/admin/telemetry/users',
    ADMIN_USERS_LIVE: '/admin/telemetry/users-live',
    ADMIN_USER_TIMELINE: (userId) => `/admin/telemetry/users/${userId}/timeline`,
    ADMIN_USER_SESSIONS: (userId) => `/admin/telemetry/users/${userId}/sessions`,
    ADMIN_FUNNELS: '/admin/telemetry/funnels',
    ADMIN_FUNNEL_ANALYZE: '/admin/telemetry/funnels/analyze',
    // Error endpoints
    ADMIN_ERRORS_SUMMARY: '/admin/telemetry/errors/summary',
    ADMIN_ERRORS_TIMELINE: '/admin/telemetry/errors/timeline',
    ADMIN_ERROR_FLOW: (errorName) => `/admin/telemetry/errors/${encodeURIComponent(errorName)}/flow`,
    ADMIN_ERROR_DETAILS: (errorName) => `/admin/telemetry/errors/${encodeURIComponent(errorName)}/details`,
    // Event discovery & presence
    ADMIN_EVENTS_DISCOVER: '/admin/telemetry/events/discover',
    ADMIN_PRESENCE_ONLINE: '/admin/telemetry/presence/online',
    // AI Insights
    ADMIN_INSIGHTS: '/admin/telemetry/insights',
    ADMIN_INSIGHTS_UNREAD: '/admin/telemetry/insights/unread-count',
    ADMIN_INSIGHT_DETAIL: (id) => `/admin/telemetry/insights/${id}`,
    ADMIN_INSIGHT_READ: (id) => `/admin/telemetry/insights/${id}/read`,
    ADMIN_INSIGHT_DISMISS: (id) => `/admin/telemetry/insights/${id}/dismiss`,
    ADMIN_INSIGHTS_DAILY_DIGEST: '/admin/telemetry/insights/daily-digest',
    ADMIN_INSIGHTS_ANALYZE: (execId) => `/admin/telemetry/insights/analyze/${execId}`,
    ADMIN_INSIGHTS_SETTINGS: '/admin/telemetry/insights/settings',
    // Health Check
    ADMIN_HEALTH: '/admin/telemetry/health',
    ADMIN_HEALTH_SUMMARY: '/admin/telemetry/health/summary',
    ADMIN_HEALTH_TIMELINE: '/admin/telemetry/health/timeline'
  }
}

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user',
  LANGUAGE: 'language',
  THEME: 'theme'
}
