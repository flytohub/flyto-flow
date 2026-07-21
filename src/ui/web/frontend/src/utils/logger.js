/**
 * Logger Utility
 * Conditional logging that only outputs in development mode
 */

const DEBUG = import.meta.env.DEV

/**
 * Logger with environment-aware log levels
 */
export const logger = {
  /**
   * Debug log - only in development
   * @param {...any} args - Arguments to log
   */
  debug: (...args) => DEBUG && console.log('[DEBUG]', ...args),

  /**
   * Info log - only in development
   * @param {...any} args - Arguments to log
   */
  info: (...args) => DEBUG && console.info('[INFO]', ...args),

  /**
   * Warning log - always shown
   * @param {...any} args - Arguments to log
   */
  warn: (...args) => console.warn('[WARN]', ...args),

  /**
   * Error log - always shown
   * @param {...any} args - Arguments to log
   */
  error: (...args) => console.error('[ERROR]', ...args),

  /**
   * Group logs - only in development
   * @param {string} label - Group label
   */
  group: (label) => DEBUG && console.group(label),

  /**
   * End group - only in development
   */
  groupEnd: () => DEBUG && console.groupEnd(),

  /**
   * Table log - only in development
   * @param {any} data - Data to display as table
   */
  table: (data) => DEBUG && console.table(data)
}

export default logger
