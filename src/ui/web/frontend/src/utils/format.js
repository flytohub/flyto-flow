/**
 * Unified Formatting Utilities
 *
 * Single source of truth for all formatting functions.
 * Import from here instead of useFormatters.js for consistency.
 */

import { getLocale } from '@/i18n'

/**
 * Get current locale for formatting
 * Falls back to browser locale if i18n not available
 */
function getCurrentLocale() {
  try {
    return getLocale() || navigator.language || 'en-US'
  } catch {
    return navigator.language || 'en-US'
  }
}

// ============================================
// Date & Time Formatting
// ============================================

/**
 * Format date with optional time
 * @param {string|number|Date} dateInput - Date input
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 */
export function formatDate(dateInput, options = {}) {
  if (!dateInput) return '-'

  const date = dateInput instanceof Date
    ? dateInput
    : new Date(dateInput)

  if (isNaN(date.getTime())) return '-'

  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options
  }

  return date.toLocaleDateString(getCurrentLocale(), defaultOptions)
}

/**
 * Format date with time
 * @param {string|number|Date} dateInput - Date input
 * @returns {string} Formatted datetime string
 */
export function formatDateTime(dateInput) {
  return formatDate(dateInput, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * Format time only (HH:MM:SS)
 * @param {string|number|Date} dateInput - Date input
 * @returns {string} Formatted time string
 */
export function formatTime(dateInput) {
  if (!dateInput) return ''

  const date = dateInput instanceof Date
    ? dateInput
    : new Date(dateInput)

  if (isNaN(date.getTime())) return ''

  return date.toLocaleTimeString(getCurrentLocale(), {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * Format relative time (e.g., "2 hours ago", "just now")
 * @param {string|number|Date} dateInput - Date input
 * @returns {string} Relative time string
 */
export function formatRelativeTime(dateInput) {
  if (!dateInput) return '-'

  const date = dateInput instanceof Date
    ? dateInput
    : new Date(dateInput)

  if (isNaN(date.getTime())) return '-'

  const now = new Date()
  const diffMs = now - date
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)
  const diffWeek = Math.floor(diffDay / 7)

  if (diffSec < 60) return 'just now'
  if (diffMin < 60) return `${diffMin}m ago`
  if (diffHour < 24) return `${diffHour}h ago`
  if (diffDay < 7) return `${diffDay}d ago`
  if (diffWeek < 4) return `${diffWeek}w ago`

  return formatDate(date)
}

// ============================================
// Number Formatting
// ============================================

/**
 * Format number with locale
 * @param {number} value - Number to format
 * @param {Object} options - Intl.NumberFormat options
 * @returns {string} Formatted number string
 */
export function formatNumber(value, options = {}) {
  if (typeof value !== 'number' || isNaN(value)) return '0'
  return new Intl.NumberFormat(getCurrentLocale(), options).format(value)
}

/**
 * Format percentage
 * @param {number} value - Value (0-100 or 0-1 based on isDecimal)
 * @param {Object} options - { isDecimal: boolean, decimals: number }
 * @returns {string} Formatted percentage string
 */
export function formatPercent(value, options = {}) {
  const { isDecimal = false, decimals = 1 } = options

  if (typeof value !== 'number' || isNaN(value)) return '0%'

  const pct = isDecimal ? value * 100 : value
  return `${pct.toFixed(decimals)}%`
}

/**
 * Format bytes to human readable size
 * @param {number} bytes - Size in bytes
 * @param {number} decimals - Decimal places (default: 2)
 * @returns {string} Formatted size string (e.g., "1.5 MB")
 */
export function formatBytes(bytes, decimals = 2) {
  if (!bytes || bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`
}

// Alias for backwards compatibility
export { formatBytes as formatFileSize }

/**
 * Format milliseconds to human-readable duration
 * @param {number} ms - Duration in milliseconds
 * @returns {string} Formatted duration (e.g., "1.5s", "2m 30s", "125ms")
 */
export function formatDuration(ms) {
  if (ms === null || ms === undefined || isNaN(ms)) return '-'
  if (ms < 1000) return `${Math.round(ms)}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  const minutes = Math.floor(ms / 60000)
  const seconds = Math.round((ms % 60000) / 1000)
  return seconds > 0 ? `${minutes}m ${seconds}s` : `${minutes}m`
}

/**
 * Format number in compact form (e.g., 1.2k, 3.5k)
 * @param {number} num - Number to format
 * @returns {string} Compact formatted string
 */
export function formatCompactNumber(num) {
  if (!num) return '0'
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num / 1000).toFixed(1)}k`
  return Math.round(num).toString()
}

/**
 * Format rating to 1 decimal place
 * @param {number} rating - Rating value
 * @returns {string} Formatted rating (e.g., "4.5")
 */
export function formatRating(rating) {
  if (typeof rating !== 'number' || isNaN(rating)) return '--'
  return rating.toFixed(1)
}

// ============================================
// Currency Formatting
// ============================================

/**
 * Format currency amount (expects dollars/major unit).
 * Backend is responsible for cents→dollars conversion.
 * @param {number} amount - Amount in dollars
 * @param {string} currency - Currency code (USD, EUR, etc.)
 * @returns {string} Formatted currency string
 */
export function formatCurrency(amount, currency = 'USD') {
  return new Intl.NumberFormat(getCurrentLocale(), {
    style: 'currency',
    currency
  }).format(amount)
}

// Alias for backwards compatibility — identical to formatCurrency
export const formatCurrencyMajor = formatCurrency

/**
 * Format a credit amount as a USD display string.
 *
 * Pure display formatter — converts credits (1 credit = $0.01)
 * to a human-readable dollar string. No business logic.
 *
 * @param {number} credits - Credit amount (integer, 1 credit = $0.01)
 * @returns {string} Formatted dollar string (e.g., "$0.50")
 */
export function formatCreditsAsUSD(credits) {
  if (!credits) return '$0.00'
  const dollars = credits / 100
  return `$${dollars.toFixed(2)}`
}

// ============================================
// String Formatting
// ============================================

/**
 * Format parameter key as human-readable label
 * Converts snake_case and camelCase to Title Case
 *
 * @example
 * formatLabel('model_id') // => 'Model Id'
 * formatLabel('maxTokens') // => 'Max Tokens'
 */
export function formatLabel(key) {
  if (!key) return ''
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/^./, str => str.toUpperCase())
    .trim()
}

// Alias for backwards compatibility
export { formatLabel as formatParamLabel }

/**
 * Truncate string with ellipsis
 * @param {string} str - String to truncate
 * @param {number} maxLength - Maximum length
 * @param {string} suffix - Suffix to add (default: '...')
 * @returns {string} Truncated string
 */
export function truncate(str, maxLength, suffix = '...') {
  if (!str || str.length <= maxLength) return str || ''
  return str.slice(0, maxLength - suffix.length) + suffix
}

/**
 * Capitalize first letter
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 */
export function capitalize(str) {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}
