/**
 * Centralized Storage Keys
 *
 * All localStorage keys used in the application.
 * This prevents typos and makes it easy to find all storage usage.
 */

export const STORAGE_KEYS = {
  // Auth
  ACCESS_TOKEN: 'access_token',
  USER: 'user',

  // Preferences
  LANGUAGE: 'language',
  THEME: 'theme',

  // Module Cache
  MODULES_ATOMIC: 'flyto_modules_atomic',
  MODULES_COMPOSITE: 'flyto_modules_composite',
  MODULES_TIERED: 'flyto_modules_tiered',

  // Templates & Tools
  LOCAL_TEMPLATES: 'flyto_local_templates',
  USER_TOOLS: 'flyto_user_tools'
}

/**
 * Cache configuration
 */
export const CACHE_CONFIG = {
  MODULES_DURATION: 30 * 60 * 1000 // 30 minutes
}

export default STORAGE_KEYS
