/**
 * UX-HINT ONLY — These validators provide instant feedback while the user types.
 * The backend is the authoritative source of truth for all validation rules.
 * Do NOT rely on these for security or data integrity.
 *
 * Form Validation Utilities
 * See GET /api/config/validation-rules.
 *
 * S-Grade: Unified form validation layer.
 * Wraps core validators for form use (returns translated string or empty).
 *
 * Usage:
 *   import { formValidators, PASSWORD_MIN_LENGTH } from '@/utils/formValidation'
 *   const error = formValidators.email(value, t)
 */

// Password validation constants
export const PASSWORD_MIN_LENGTH = 8

import {
  validateEmail as coreValidateEmail,
  validateURL as coreValidateURL,
  validateNumberRange as coreValidateNumberRange
} from './templateBuilder/validators'

/**
 * Translate validation result to form error string
 * @param {Object} result - { valid, errorKey, params }
 * @param {Function} t - i18n translate function
 * @returns {string} Error message or empty string
 */
function translateResult(result, t) {
  if (result.valid) return ''
  return t(result.errorKey, result.params) || result.errorKey
}

/**
 * Form-friendly validators
 * Each returns empty string (valid) or translated error message
 */
export const formValidators = {
  /**
   * Validate required field
   * @param {any} value
   * @param {Function} t - i18n translate function
   * @returns {string}
   */
  required(value, t) {
    if (!value || (typeof value === 'string' && !value.trim())) {
      return t('validation.required')
    }
    return ''
  },

  /**
   * Validate email format
   * @param {string} value
   * @param {Function} t
   * @returns {string}
   */
  email(value, t) {
    if (!value) return t('validation.required')
    const result = coreValidateEmail(value)
    if (!result.valid) {
      return t('validation.invalidEmail')
    }
    return ''
  },

  /**
   * Validate URL format
   * @param {string} value
   * @param {Function} t
   * @returns {string}
   */
  url(value, t) {
    if (!value) return ''  // URL often optional
    const result = coreValidateURL(value)
    return translateResult(result, t)
  },

  /**
   * Validate min length
   * @param {string} value
   * @param {number} min
   * @param {Function} t
   * @returns {string}
   */
  minLength(value, min, t) {
    if (!value) return t('validation.required')
    if (value.length < min) {
      return t('validation.minLength', { min })
    }
    return ''
  },

  /**
   * Validate max length
   * @param {string} value
   * @param {number} max
   * @param {Function} t
   * @returns {string}
   */
  maxLength(value, max, t) {
    if (value && value.length > max) {
      return t('validation.maxLength', { max })
    }
    return ''
  },

  /**
   * Validate number range
   * @param {number} value
   * @param {number} min
   * @param {number} max
   * @param {Function} t
   * @returns {string}
   */
  numberRange(value, min, max, t) {
    const result = coreValidateNumberRange(value, min, max)
    return translateResult(result, t)
  },

  /**
   * Validate alphanumeric with underscore (for usernames)
   * @param {string} value
   * @param {Function} t
   * @returns {string}
   */
  alphanumeric(value, t) {
    if (!value) return t('validation.required')
    if (!/^[a-zA-Z0-9_]+$/.test(value)) {
      return t('validation.alphanumeric')
    }
    return ''
  },

  /**
   * Validate password strength
   * @param {string} value
   * @param {Object} options - { minLength, requireUppercase, requireLowercase, requireNumber }
   * @param {Function} t
   * @returns {string}
   */
  password(value, options, t) {
    const {
      minLength = PASSWORD_MIN_LENGTH,
      requireUppercase = true,
      requireLowercase = true,
      requireNumber = true
    } = options || {}

    if (!value) return t('validation.required')
    if (value.length < minLength) {
      return t('validation.minLength', { min: minLength })
    }
    if (requireUppercase && !/[A-Z]/.test(value)) {
      return t('validation.needsUppercase')
    }
    if (requireLowercase && !/[a-z]/.test(value)) {
      return t('validation.needsLowercase')
    }
    if (requireNumber && !/\d/.test(value)) {
      return t('validation.needsNumber')
    }
    return ''
  },

  /**
   * Validate password confirmation matches
   * @param {string} value
   * @param {string} password
   * @param {Function} t
   * @returns {string}
   */
  confirmPassword(value, password, t) {
    if (!value) return t('validation.required')
    if (value !== password) {
      return t('validation.passwordMismatch')
    }
    return ''
  }
}

export default formValidators
