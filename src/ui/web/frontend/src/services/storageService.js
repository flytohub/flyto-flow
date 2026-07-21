/**
 * Storage Service
 * Centralized wrapper for localStorage and sessionStorage operations.
 * Provides consistent API with JSON serialization and error handling.
 */

/**
 * Safe JSON parse with fallback
 * @param {string} value - JSON string to parse
 * @param {*} fallback - Fallback value if parsing fails
 * @returns {*} Parsed value or fallback
 */
function safeParse(value, fallback = null) {
  if (value === null || value === undefined) return fallback
  try {
    return JSON.parse(value)
  } catch {
    return value // Return as-is if not valid JSON
  }
}

/**
 * Safe JSON stringify
 * @param {*} value - Value to stringify
 * @returns {string} JSON string
 */
function safeStringify(value) {
  if (typeof value === 'string') return value
  return JSON.stringify(value)
}

/**
 * Create storage wrapper for given storage type
 * @param {Storage} storage - localStorage or sessionStorage
 * @returns {Object} Storage wrapper
 */
function createStorageWrapper(storage) {
  return {
    /**
     * Get value from storage
     * @param {string} key - Storage key
     * @param {*} fallback - Fallback value if key not found
     * @returns {*} Stored value or fallback
     */
    get(key, fallback = null) {
      try {
        const value = storage.getItem(key)
        return safeParse(value, fallback)
      } catch {
        return fallback
      }
    },

    /**
     * Get raw string value from storage
     * @param {string} key - Storage key
     * @returns {string|null} Raw stored value
     */
    getRaw(key) {
      try {
        return storage.getItem(key)
      } catch {
        return null
      }
    },

    /**
     * Set value in storage
     * @param {string} key - Storage key
     * @param {*} value - Value to store
     * @returns {boolean} Success status
     */
    set(key, value) {
      try {
        storage.setItem(key, safeStringify(value))
        return true
      } catch {
        return false
      }
    },

    /**
     * Remove value from storage
     * @param {string} key - Storage key
     * @returns {boolean} Success status
     */
    remove(key) {
      try {
        storage.removeItem(key)
        return true
      } catch {
        return false
      }
    },

    /**
     * Check if key exists in storage
     * @param {string} key - Storage key
     * @returns {boolean} Whether key exists
     */
    has(key) {
      try {
        return storage.getItem(key) !== null
      } catch {
        return false
      }
    },

    /**
     * Clear all values from storage
     * @returns {boolean} Success status
     */
    clear() {
      try {
        storage.clear()
        return true
      } catch {
        return false
      }
    }
  }
}

// Export storage wrappers
export const localStore = createStorageWrapper(localStorage)
export const sessionStore = createStorageWrapper(sessionStorage)

// Default export for convenience
export const storageService = {
  local: localStore,
  session: sessionStore
}

export default storageService
