import { describe, it, expect, vi } from 'vitest'

vi.mock('@/i18n', () => ({
  getLocale: () => 'en-US'
}))

import { useFormatters } from '@/composables/useFormatters'

describe('useFormatters', () => {
  const fmt = useFormatters()

  it('returns all expected formatter functions', () => {
    expect(typeof fmt.formatDate).toBe('function')
    expect(typeof fmt.formatDateTime).toBe('function')
    expect(typeof fmt.formatTime).toBe('function')
    expect(typeof fmt.formatRelativeTime).toBe('function')
    expect(typeof fmt.formatNumber).toBe('function')
    expect(typeof fmt.formatPercent).toBe('function')
    expect(typeof fmt.formatBytes).toBe('function')
    expect(typeof fmt.formatCurrency).toBe('function')
    expect(typeof fmt.formatCurrencyMajor).toBe('function')
    expect(typeof fmt.formatParamLabel).toBe('function')
    expect(typeof fmt.truncate).toBe('function')
    expect(typeof fmt.capitalize).toBe('function')
  })

  describe('formatDate', () => {
    it('returns "-" for falsy input', () => {
      expect(fmt.formatDate(null)).toBe('-')
      expect(fmt.formatDate(undefined)).toBe('-')
      expect(fmt.formatDate('')).toBe('-')
    })

    it('returns "-" for invalid date', () => {
      expect(fmt.formatDate('not-a-date')).toBe('-')
    })

    it('formats a valid date string', () => {
      const result = fmt.formatDate('2025-01-15')
      expect(result).toBeTruthy()
      expect(result).not.toBe('-')
    })
  })

  describe('formatNumber', () => {
    it('returns "0" for non-number input', () => {
      expect(fmt.formatNumber(null)).toBe('0')
      expect(fmt.formatNumber('abc')).toBe('0')
      expect(fmt.formatNumber(NaN)).toBe('0')
    })

    it('formats numbers with locale', () => {
      const result = fmt.formatNumber(1234.5)
      expect(result).toContain('1')
      expect(result).toContain('234')
    })
  })

  describe('formatPercent', () => {
    it('returns "0%" for non-number', () => {
      expect(fmt.formatPercent(null)).toBe('0%')
      expect(fmt.formatPercent(NaN)).toBe('0%')
    })

    it('formats a percentage', () => {
      expect(fmt.formatPercent(42.567)).toBe('42.6%')
    })

    it('handles decimal mode', () => {
      // 0.5 as decimal => 50.0%
      const result = fmt.formatPercent(0.5, { isDecimal: true })
      expect(result).toBe('50.0%')
    })
  })

  describe('formatBytes', () => {
    it('returns "0 Bytes" for zero/falsy', () => {
      expect(fmt.formatBytes(0)).toBe('0 Bytes')
      expect(fmt.formatBytes(null)).toBe('0 Bytes')
    })

    it('formats bytes', () => {
      expect(fmt.formatBytes(500)).toBe('500 Bytes')
    })

    it('formats kilobytes', () => {
      expect(fmt.formatBytes(1024)).toBe('1 KB')
    })

    it('formats megabytes', () => {
      expect(fmt.formatBytes(1048576)).toBe('1 MB')
    })

    it('formats with custom decimals', () => {
      expect(fmt.formatBytes(1536, 1)).toBe('1.5 KB')
    })
  })

  describe('formatParamLabel', () => {
    it('returns empty for falsy input', () => {
      expect(fmt.formatParamLabel('')).toBe('')
      expect(fmt.formatParamLabel(null)).toBe('')
    })

    it('converts snake_case to Title Case', () => {
      expect(fmt.formatParamLabel('model_id')).toBe('Model id')
    })

    it('converts camelCase to separate words', () => {
      expect(fmt.formatParamLabel('maxTokens')).toBe('Max Tokens')
    })
  })

  describe('truncate', () => {
    it('returns empty string for falsy input', () => {
      expect(fmt.truncate(null, 10)).toBe('')
      expect(fmt.truncate('', 10)).toBe('')
    })

    it('returns string as-is if under maxLength', () => {
      expect(fmt.truncate('hello', 10)).toBe('hello')
    })

    it('truncates with ellipsis', () => {
      expect(fmt.truncate('hello world this is long', 10)).toBe('hello w...')
    })
  })

  describe('capitalize', () => {
    it('returns empty for falsy input', () => {
      expect(fmt.capitalize('')).toBe('')
      expect(fmt.capitalize(null)).toBe('')
    })

    it('capitalizes first letter', () => {
      expect(fmt.capitalize('hello')).toBe('Hello')
    })

    it('does not change already capitalized', () => {
      expect(fmt.capitalize('Hello')).toBe('Hello')
    })
  })
})
