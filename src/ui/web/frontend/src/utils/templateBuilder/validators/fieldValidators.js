/**
 * UX-HINT ONLY — These validators provide instant feedback while the user types.
 * The backend is the authoritative source of truth for all validation rules.
 * Do NOT rely on these for security or data integrity.
 *
 * Field Validators
 * See GET /api/config/validation-rules.
 *
 * S-Grade: Field value validation.
 * Single responsibility: Validate field values and formats.
 */

import { createResult } from './utils'

/**
 * Validate field value (for required field validation)
 * @param {any} value - Field value
 * @param {boolean} required - Whether required
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateFieldValue(value, required = false) {
  if (!required) {
    return createResult(true)
  }

  if (value === null || value === undefined) {
    return createResult(false, 'validation.field.required')
  }

  if (typeof value === 'string' && value.trim() === '') {
    return createResult(false, 'validation.field.cannotBeEmpty')
  }

  if (Array.isArray(value) && value.length === 0) {
    return createResult(false, 'validation.field.selectAtLeastOne')
  }

  return createResult(true)
}

/**
 * Validate email format
 * @param {string} email - Email address
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateEmail(email) {
  if (!email || typeof email !== 'string') {
    return createResult(false, 'validation.email.empty')
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

  if (!emailRegex.test(email)) {
    return createResult(false, 'validation.email.invalid')
  }

  return createResult(true)
}

/**
 * Validate URL format
 * @param {string} url - URL address
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateURL(url) {
  if (!url || typeof url !== 'string') {
    return createResult(false, 'validation.url.empty')
  }

  try {
    new URL(url)
    return createResult(true)
  } catch (e) {
    return createResult(false, 'validation.url.invalid')
  }
}

/**
 * Validate number range
 * @param {number} value - Number value
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateNumberRange(value, min = -Infinity, max = Infinity) {
  const num = parseFloat(value)

  if (isNaN(num)) {
    return createResult(false, 'validation.number.invalid')
  }

  if (num < min) {
    return createResult(false, 'validation.number.tooSmall', { min })
  }

  if (num > max) {
    return createResult(false, 'validation.number.tooLarge', { max })
  }

  return createResult(true)
}
