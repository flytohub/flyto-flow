/**
 * Formatters Composable
 *
 * Provides formatting utilities as a composable.
 * This is a wrapper around utils/format.js for use in Vue components.
 *
 * For direct usage outside components, import from '@/utils/format' instead.
 */

import {
  formatDate,
  formatDateTime,
  formatTime,
  formatRelativeTime,
  formatNumber,
  formatPercent,
  formatBytes,
  formatCurrency,
  formatCurrencyMajor,
  formatParamLabel,
  truncate,
  capitalize
} from '@/utils/format'

/**
 * Create formatters composable
 * @returns {Object} Formatter functions
 */
export function useFormatters() {
  return {
    formatDate,
    formatDateTime,
    formatTime,
    formatRelativeTime,
    formatNumber,
    formatPercent,
    formatBytes,
    formatCurrency,
    formatCurrencyMajor,
    formatParamLabel,
    truncate,
    capitalize
  }
}

// Re-export all functions for direct import
export {
  formatDate,
  formatDateTime,
  formatTime,
  formatRelativeTime,
  formatNumber,
  formatPercent,
  formatBytes,
  formatCurrency,
  formatCurrencyMajor,
  formatParamLabel,
  truncate,
  capitalize
}
