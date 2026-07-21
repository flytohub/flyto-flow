/**
 * Default Configuration Values
 * Sensible defaults for all configurable options
 */

export const DEFAULTS = {
  // Application Info (contact, branding)
  APP: {
    NAME: 'Flyto2',
    SUPPORT_EMAIL: 'support@flyto2.com',
    WEBSITE: 'https://flyto2.com',
    DOCS_URL: 'https://docs.flyto2.com'
  },

  // Home Page Statistics (marketing/display purposes)
  HOME_STATS: {
    ACTIVE_USERS: 5000,
    WORKFLOWS_CREATED: 12000,
    SUCCESS_RATE: 98,
    TOTAL_EXECUTIONS: 150000
  },

  API: {
    PORT: 9000,
    HOST: '127.0.0.1',
    TIMEOUT: 30000
  },

  FRONTEND: {
    PORT: 3000
  },

  RETRY: {
    MAX_RETRIES: 3,
    DELAY: 1000,
    RETRYABLE_STATUSES: [408, 429, 500, 502, 503, 504]
  },

  WEBSOCKET: {
    RECONNECT_INTERVAL: 3000,
    MAX_RECONNECT_ATTEMPTS: 5
  },

  // Agent (Runner Device Polling)
  AGENT: {
    POLL_INTERVAL_MS: 5000,       // Poll inbox every 5 seconds
    HEARTBEAT_INTERVAL_MS: 30000, // Send heartbeat every 30 seconds
    LEASE_DURATION_MS: 300000,    // 5 minute lease
    MAX_RETRIES: 3,               // Max event retries
    BACKOFF_BASE_MS: 30000,       // 30 second base backoff
    BACKOFF_MAX_MS: 300000,       // 5 minute max backoff
    ONLINE_TIMEOUT_MS: 60000      // Device considered offline after 60s
  },

  TIMING: {
    // Toast notifications
    TOAST_DURATION: 3000,
    TOAST_DURATION_ERROR: 5000,

    // Debounce/Throttle
    DEBOUNCE_DELAY: 300,
    DEBOUNCE_SEARCH: 300,
    DEBOUNCE_VALIDATION: 500,     // Validation debounce (e.g. cron expression)
    SYNC_DEBOUNCE: 100,           // Short debounce for sync operations

    // Polling intervals
    POLL_NOTIFICATIONS: 60000,       // 60 seconds
    POLL_CHAT_CONVERSATIONS: 10000,  // 10 seconds
    POLL_CHAT_MESSAGES: 3000,        // 3 seconds
    POLL_UNREAD_MESSAGES: 30000,     // 30 seconds (navbar badge)
    MODULE_SYNC_POLL: 30000,         // 30 seconds
    MODULE_SYNC_RECONNECT: 5000,     // 5 seconds

    // UI timing
    ANIMATION_DURATION: 200,
    ANIMATION_INIT: 100,          // Quick init delay
    ANIMATION_STAGGER: 500,       // Stagger delay for sequential animations
    TYPING_INDICATOR: 2000,
    TYPING_DELAY: 500,            // Typing effect delay
    TYPE_SPEED: 100,              // Typing effect character speed (ms per char)
    PARTICLE_INTERVAL: 2000,      // Particle animation interval
    RECONNECT_DELAY: 3000,
    COPY_FEEDBACK: 2000,          // Show "copied" indicator
    POLL_RETRY_DELAY: 1000,       // Retry delay for polling
    SUCCESS_MESSAGE: 5000,        // Success message display time
    AUTO_SAVE_DELAY: 1500,        // Auto-save debounce delay
    POLL_TRIGGERS: 30000           // 30 seconds (triggers indicator)
  },

  // Node/Component-specific timeouts
  TIMEOUTS: {
    HTTP_NODE: 30000,             // HTTP node request timeout
    SUBFLOW_NODE: 300000,         // Subflow execution timeout (5 minutes)
    JOIN_NODE: 60000,             // Join node timeout (1 minute)
    CDN_FETCH: 5000,              // CDN/translation fetch timeout
    AUTH_CACHE_TTL: 10000,        // Auth cache TTL
    ASYNC_COMPONENT: 10000        // Async component loading timeout
  },

  // Cache TTL values
  CACHE_TTL: {
    MANIFEST: 0,                            // Always fetch fresh (tiny file, version-gates translations)
    TRANSLATION: 24 * 60 * 60 * 1000,      // 24 hours (was 7 days — shorter TTL ensures hotfixes propagate within a day)
    PLATFORM_CONFIG: 5 * 60 * 1000         // 5 minutes
  },

  LIMITS: {
    MAX_FILE_SIZE: 10 * 1024 * 1024,  // 10MB
    MAX_IMAGE_SIZE: 2 * 1024 * 1024,  // 2MB for images
    MAX_AVATAR_SIZE: 5 * 1024 * 1024, // 5MB for avatars
    MAX_LOG_ENTRIES: 1000,
    MAX_SEARCH_RESULTS: 100,
    MAX_POLL_ATTEMPTS: 30,           // Max polling attempts before timeout
    MAX_KNOWN_MESSAGES: 1000,        // Max cached message IDs per conversation
    MAX_TOOL_ATTEMPTS: 120,          // Max tool execution attempts
    PAGE_SIZE_DEFAULT: 12,
    PAGE_SIZE_MAX: 100
  },

  PAGINATION: {
    DEFAULT: 20,
    SMALL: 10,
    MARKETPLACE: 12,
    ADMIN: 20,
    PLUGINS: 24,
    CHAT: 50,
    AUDIT: 50,
    FEATURED_LIMIT: 3,
    MAX_PAGE_SIZE: 100
  },

  STORAGE_KEYS: {
    // Auth
    AUTH_TOKEN: 'flyto_auth_token',
    REFRESH_TOKEN: 'flyto_refresh_token',
    USER_DATA: 'flyto_user_data',

    // UI State
    SIDEBAR_COLLAPSED: 'flyto_sidebar_collapsed',
    THEME: 'flyto_theme',
    LOCALE: 'flyto_locale',

    // Module Cache
    MODULE_VERSION: 'flyto_module_version',
    MODULE_CACHE_PREFIX: 'flyto_module_cache_',
    MODULE_SYNC_TIMESTAMP: 'flyto_module_sync_timestamp',

    // Template Builder
    BUILDER_DRAFT: 'flyto_builder_draft',
    BUILDER_SETTINGS: 'flyto_builder_settings',

    // Feature Flags
    DEBUG_MODE: 'flyto_debug_mode',

    // User Preferences
    RECENT_TEMPLATES: 'flyto_recent_templates',
    FAVORITE_MODULES: 'flyto_favorite_modules'
  }
}

export const getDefaultApiUrl = () => {
  return `http://${DEFAULTS.API.HOST}:${DEFAULTS.API.PORT}`
}

/**
 * Get WebSocket URL from API URL
 * @param {string} apiBaseUrl - API base URL (http:// or https://)
 * @returns {string} WebSocket base URL (ws:// or wss://)
 */
export const getWebSocketUrl = (apiBaseUrl) => {
  if (!apiBaseUrl) {
    // Empty base = same origin; derive ws:// from current page location
    const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = typeof window !== 'undefined' ? window.location.host : `${DEFAULTS.API.HOST}:${DEFAULTS.API.PORT}`
    return `${protocol}//${host}`
  }
  return apiBaseUrl.replace(/^http/, 'ws')
}
