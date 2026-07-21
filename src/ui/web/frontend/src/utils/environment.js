/**
 * Environment Detection Utilities
 */

/**
 * Check if running in development mode
 * @returns {boolean}
 */
export function isDevelopment() {
  return import.meta.env.DEV === true
}

export default {
  isDevelopment
}
