/**
 * Local Flyto2 Flow defaults. Extended editions provide their own adapter.
 */
export const DEFAULTS = {
  APP: {
    NAME: 'Flyto2 Flow'
  },
  API: {
    PORT: 9000,
    HOST: '127.0.0.1',
    TIMEOUT: 30000
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
  TIMING: {
    TOAST_DURATION: 3000,
    TOAST_DURATION_ERROR: 5000,
    DEBOUNCE_DELAY: 300,
    SYNC_DEBOUNCE: 100,
    MODULE_SYNC_POLL: 30000,
    MODULE_SYNC_RECONNECT: 5000,
    RECONNECT_DELAY: 3000,
    AUTO_SAVE_DELAY: 1500,
    POLL_TRIGGERS: 30000,
    ANIMATION_STAGGER: 500
  },
  TIMEOUTS: {
    HTTP_NODE: 30000,
    SUBFLOW_NODE: 300000,
    JOIN_NODE: 60000
  },
  LIMITS: {
    MAX_IMAGE_SIZE: 2 * 1024 * 1024
  },
  STORAGE_KEYS: {
    MODULE_VERSION: 'flyto_module_version',
    MODULE_CACHE_PREFIX: 'flyto_module_cache_'
  }
}

export const getDefaultApiUrl = () =>
  `http://${DEFAULTS.API.HOST}:${DEFAULTS.API.PORT}`

export const getWebSocketUrl = (apiBaseUrl) => {
  if (!apiBaseUrl) {
    const protocol =
      typeof window !== 'undefined' && window.location.protocol === 'https:'
        ? 'wss:'
        : 'ws:'
    const host =
      typeof window !== 'undefined'
        ? window.location.host
        : `${DEFAULTS.API.HOST}:${DEFAULTS.API.PORT}`
    return `${protocol}//${host}`
  }
  return apiBaseUrl.replace(/^http/, 'ws')
}
