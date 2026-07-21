import { describe, it, expect, vi } from 'vitest'

// Mock the core validators
vi.mock('@/utils/templateBuilder/validators', () => ({
  validateEmail: vi.fn((email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return { valid: emailRegex.test(email), errorKey: 'validation.email.invalid' }
  }),
  validateURL: vi.fn((url) => {
    try {
      new URL(url)
      return { valid: true }
    } catch {
      return { valid: false, errorKey: 'validation.url.invalid', params: {} }
    }
  }),
  validateNumberRange: vi.fn((value, min, max) => {
    const num = parseFloat(value)
    if (isNaN(num)) return { valid: false, errorKey: 'validation.number.invalid', params: {} }
    if (num < min) return { valid: false, errorKey: 'validation.number.tooSmall', params: { min } }
    if (num > max) return { valid: false, errorKey: 'validation.number.tooLarge', params: { max } }
    return { valid: true }
  })
}))

import { formValidators, PASSWORD_MIN_LENGTH } from '@/utils/formValidation'

// Simple mock t function
const t = (key, params) => params ? `${key}:${JSON.stringify(params)}` : key

describe('formValidation utilities', () => {
  describe('PASSWORD_MIN_LENGTH', () => {
    it('is 8', () => {
      expect(PASSWORD_MIN_LENGTH).toBe(8)
    })
  })

  describe('formValidators.required', () => {
    it('returns error for falsy values', () => {
      expect(formValidators.required(null, t)).toBe('validation.required')
      expect(formValidators.required('', t)).toBe('validation.required')
      expect(formValidators.required(undefined, t)).toBe('validation.required')
    })

    it('returns error for whitespace-only string', () => {
      expect(formValidators.required('   ', t)).toBe('validation.required')
    })

    it('returns empty string for valid values', () => {
      expect(formValidators.required('hello', t)).toBe('')
      expect(formValidators.required(42, t)).toBe('')
    })
  })

  describe('formValidators.email', () => {
    it('returns required error for empty', () => {
      expect(formValidators.email('', t)).toBe('validation.required')
      expect(formValidators.email(null, t)).toBe('validation.required')
    })

    it('returns error for invalid email', () => {
      expect(formValidators.email('notanemail', t)).toBe('validation.invalidEmail')
    })

    it('returns empty string for valid email', () => {
      expect(formValidators.email('test@flyto2.com', t)).toBe('')
    })
  })

  describe('formValidators.url', () => {
    it('returns empty for empty value (optional)', () => {
      expect(formValidators.url('', t)).toBe('')
      expect(formValidators.url(null, t)).toBe('')
    })

    it('returns error for invalid URL', () => {
      const result = formValidators.url('not-a-url', t)
      expect(result).not.toBe('')
    })

    it('returns empty for valid URL', () => {
      expect(formValidators.url('https://flyto2.com', t)).toBe('')
    })
  })

  describe('formValidators.minLength', () => {
    it('returns required for empty', () => {
      expect(formValidators.minLength('', 5, t)).toBe('validation.required')
      expect(formValidators.minLength(null, 5, t)).toBe('validation.required')
    })

    it('returns error when too short', () => {
      const result = formValidators.minLength('ab', 5, t)
      expect(result).toContain('validation.minLength')
    })

    it('returns empty when meets minimum', () => {
      expect(formValidators.minLength('hello', 5, t)).toBe('')
      expect(formValidators.minLength('hello world', 5, t)).toBe('')
    })
  })

  describe('formValidators.maxLength', () => {
    it('returns empty for null/short values', () => {
      expect(formValidators.maxLength(null, 10, t)).toBe('')
      expect(formValidators.maxLength('hi', 10, t)).toBe('')
    })

    it('returns error when too long', () => {
      const result = formValidators.maxLength('hello world', 5, t)
      expect(result).toContain('validation.maxLength')
    })
  })

  describe('formValidators.numberRange', () => {
    it('returns error for non-number', () => {
      const result = formValidators.numberRange('abc', 0, 100, t)
      expect(result).not.toBe('')
    })

    it('returns error for below range', () => {
      const result = formValidators.numberRange(-5, 0, 100, t)
      expect(result).not.toBe('')
    })

    it('returns error for above range', () => {
      const result = formValidators.numberRange(200, 0, 100, t)
      expect(result).not.toBe('')
    })

    it('returns empty for in-range value', () => {
      expect(formValidators.numberRange(50, 0, 100, t)).toBe('')
    })
  })

  describe('formValidators.alphanumeric', () => {
    it('returns required for empty', () => {
      expect(formValidators.alphanumeric('', t)).toBe('validation.required')
    })

    it('returns error for invalid characters', () => {
      expect(formValidators.alphanumeric('hello world', t)).toBe('validation.alphanumeric')
      expect(formValidators.alphanumeric('test@user', t)).toBe('validation.alphanumeric')
    })

    it('accepts alphanumeric with underscore', () => {
      expect(formValidators.alphanumeric('test_user123', t)).toBe('')
      expect(formValidators.alphanumeric('ABC', t)).toBe('')
    })
  })

  describe('formValidators.password', () => {
    it('returns required for empty', () => {
      expect(formValidators.password('', {}, t)).toBe('validation.required')
    })

    it('returns error for too short', () => {
      const result = formValidators.password('Aa1', {}, t)
      expect(result).toContain('validation.minLength')
    })

    it('returns error when missing uppercase', () => {
      expect(formValidators.password('abcdefg1', {}, t)).toBe('validation.needsUppercase')
    })

    it('returns error when missing lowercase', () => {
      expect(formValidators.password('ABCDEFG1', {}, t)).toBe('validation.needsLowercase')
    })

    it('returns error when missing number', () => {
      expect(formValidators.password('Abcdefgh', {}, t)).toBe('validation.needsNumber')
    })

    it('accepts valid password', () => {
      expect(formValidators.password('Password1', {}, t)).toBe('')
    })

    it('respects custom options', () => {
      expect(formValidators.password('abc', { minLength: 2, requireUppercase: false, requireNumber: false }, t)).toBe('')
    })

    it('handles null options', () => {
      expect(formValidators.password('Password1', null, t)).toBe('')
    })
  })

  describe('formValidators.confirmPassword', () => {
    it('returns required for empty', () => {
      expect(formValidators.confirmPassword('', 'pass', t)).toBe('validation.required')
    })

    it('returns mismatch error', () => {
      expect(formValidators.confirmPassword('abc', 'def', t)).toBe('validation.passwordMismatch')
    })

    it('returns empty when matching', () => {
      expect(formValidators.confirmPassword('password', 'password', t)).toBe('')
    })
  })
})
