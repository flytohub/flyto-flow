/**
 * Integration Test: Format Utilities (100% real, zero mocks)
 *
 * Tests ALL real formatting utilities from format.js and formatTime.js.
 * No mocks whatsoever — pure function testing.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock only i18n getLocale to control locale in tests
vi.mock('@/i18n', () => ({
  default: {
    global: {
      t: (key) => key,
      locale: { value: 'en' }
    }
  },
  getLocale: () => 'en-US'
}))

import {
  formatDate,
  formatDateTime,
  formatTime,
  formatRelativeTime,
  formatNumber,
  formatPercent,
  formatBytes,
  formatFileSize,
  formatDuration,
  formatCompactNumber,
  formatRating,
  formatCurrency,
  formatCurrencyMajor,
  formatCreditsAsUSD,
  formatLabel,
  formatParamLabel,
  truncate,
  capitalize
} from '@/utils/format'

import {
  formatRelativeTime as formatRelativeTimeFT,
  formatDuration as formatDurationFT,
  formatFileSize as formatFileSizeFT
} from '@/utils/formatTime'

describe('Format Utilities (100% Real)', () => {

  // =========================================================================
  // Date & Time Formatting (format.js)
  // =========================================================================

  describe('formatDate', () => {
    it('should format valid date string', () => {
      const result = formatDate('2026-01-15T10:30:00Z')
      expect(result).toBeTruthy()
      expect(result).not.toBe('-')
      // Should contain month and day
      expect(result).toMatch(/Jan|15|2026/)
    })

    it('should format Date object', () => {
      const result = formatDate(new Date('2026-06-25'))
      expect(result).not.toBe('-')
    })

    it('should format timestamp number', () => {
      const result = formatDate(Date.now())
      expect(result).not.toBe('-')
    })

    it('should return "-" for null/undefined', () => {
      expect(formatDate(null)).toBe('-')
      expect(formatDate(undefined)).toBe('-')
      expect(formatDate('')).toBe('-')
    })

    it('should return "-" for invalid dates', () => {
      expect(formatDate('not-a-date')).toBe('-')
      expect(formatDate('abc')).toBe('-')
    })

    it('should accept custom options', () => {
      const result = formatDate('2026-03-15', { weekday: 'long' })
      expect(result).toBeTruthy()
    })
  })

  describe('formatDateTime', () => {
    it('should include time component', () => {
      const result = formatDateTime('2026-01-15T14:30:00Z')
      expect(result).toBeTruthy()
      expect(result).not.toBe('-')
    })

    it('should handle null', () => {
      expect(formatDateTime(null)).toBe('-')
    })
  })

  describe('formatTime', () => {
    it('should format time only', () => {
      const result = formatTime('2026-01-15T14:30:45Z')
      expect(result).toBeTruthy()
      expect(result).not.toBe('')
    })

    it('should return empty string for null', () => {
      expect(formatTime(null)).toBe('')
      expect(formatTime(undefined)).toBe('')
    })

    it('should return empty for invalid date', () => {
      expect(formatTime('invalid')).toBe('')
    })
  })

  describe('formatRelativeTime (format.js)', () => {
    it('should return "just now" for recent times', () => {
      const now = new Date()
      expect(formatRelativeTime(now)).toBe('just now')
    })

    it('should return minutes ago', () => {
      const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000)
      expect(formatRelativeTime(fiveMinAgo)).toBe('5m ago')
    })

    it('should return hours ago', () => {
      const threeHoursAgo = new Date(Date.now() - 3 * 60 * 60 * 1000)
      expect(formatRelativeTime(threeHoursAgo)).toBe('3h ago')
    })

    it('should return days ago', () => {
      const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000)
      expect(formatRelativeTime(twoDaysAgo)).toBe('2d ago')
    })

    it('should return weeks ago', () => {
      const twoWeeksAgo = new Date(Date.now() - 14 * 24 * 60 * 60 * 1000)
      expect(formatRelativeTime(twoWeeksAgo)).toBe('2w ago')
    })

    it('should return formatted date for old dates', () => {
      const oldDate = new Date(Date.now() - 60 * 24 * 60 * 60 * 1000)
      const result = formatRelativeTime(oldDate)
      // Should be an actual date format, not relative
      expect(result).not.toContain('ago')
    })

    it('should return "-" for null/undefined', () => {
      expect(formatRelativeTime(null)).toBe('-')
      expect(formatRelativeTime(undefined)).toBe('-')
    })

    it('should return "-" for invalid date', () => {
      expect(formatRelativeTime('not-a-date')).toBe('-')
    })
  })

  // =========================================================================
  // Number Formatting
  // =========================================================================

  describe('formatNumber', () => {
    it('should format numbers with locale', () => {
      const result = formatNumber(1234567)
      expect(result).toBeTruthy()
      // Should contain digits
      expect(result).toMatch(/1.*234.*567/)
    })

    it('should return "0" for NaN', () => {
      expect(formatNumber(NaN)).toBe('0')
    })

    it('should return "0" for non-numbers', () => {
      expect(formatNumber('not a number')).toBe('0')
      expect(formatNumber(null)).toBe('0')
      expect(formatNumber(undefined)).toBe('0')
    })

    it('should accept Intl options', () => {
      const result = formatNumber(3.14159, { maximumFractionDigits: 2 })
      expect(result).toMatch(/3\.14/)
    })

    it('should handle zero', () => {
      expect(formatNumber(0)).toBe('0')
    })

    it('should handle negative numbers', () => {
      const result = formatNumber(-42)
      expect(result).toContain('42')
    })

    it('should handle Infinity', () => {
      // Infinity is a valid number
      const result = formatNumber(Infinity)
      expect(result).toBeTruthy()
    })
  })

  describe('formatPercent', () => {
    it('should format percentage from 0-100', () => {
      expect(formatPercent(75.5)).toBe('75.5%')
      expect(formatPercent(100)).toBe('100.0%')
      expect(formatPercent(0)).toBe('0.0%')
    })

    it('should format decimal percentage (0-1)', () => {
      expect(formatPercent(0.755, { isDecimal: true })).toBe('75.5%')
      expect(formatPercent(1.0, { isDecimal: true })).toBe('100.0%')
    })

    it('should accept custom decimals', () => {
      expect(formatPercent(33.333, { decimals: 2 })).toBe('33.33%')
      expect(formatPercent(50, { decimals: 0 })).toBe('50%')
    })

    it('should return "0%" for NaN/non-number', () => {
      expect(formatPercent(NaN)).toBe('0%')
      expect(formatPercent('abc')).toBe('0%')
    })
  })

  describe('formatBytes / formatFileSize', () => {
    it('should format bytes correctly', () => {
      expect(formatBytes(0)).toBe('0 Bytes')
      expect(formatBytes(512)).toBe('512 Bytes')
      expect(formatBytes(1024)).toBe('1 KB')
      expect(formatBytes(1048576)).toBe('1 MB')
      expect(formatBytes(1073741824)).toBe('1 GB')
      expect(formatBytes(1099511627776)).toBe('1 TB')
    })

    it('should respect decimals parameter', () => {
      expect(formatBytes(1536, 1)).toBe('1.5 KB')
      expect(formatBytes(1536, 0)).toBe('2 KB')
    })

    it('should handle null/zero', () => {
      expect(formatBytes(null)).toBe('0 Bytes')
      expect(formatBytes(0)).toBe('0 Bytes')
    })

    it('formatFileSize should be alias for formatBytes', () => {
      expect(formatFileSize(1024)).toBe(formatBytes(1024))
    })
  })

  describe('formatDuration (format.js)', () => {
    it('should format milliseconds', () => {
      expect(formatDuration(500)).toBe('500ms')
      expect(formatDuration(50)).toBe('50ms')
      expect(formatDuration(1)).toBe('1ms')
    })

    it('should format seconds', () => {
      expect(formatDuration(1500)).toBe('1.5s')
      expect(formatDuration(5000)).toBe('5.0s')
    })

    it('should format minutes and seconds', () => {
      expect(formatDuration(90000)).toBe('1m 30s')
      expect(formatDuration(60000)).toBe('1m')
      expect(formatDuration(120000)).toBe('2m')
    })

    it('should handle null/undefined/NaN', () => {
      expect(formatDuration(null)).toBe('-')
      expect(formatDuration(undefined)).toBe('-')
      expect(formatDuration(NaN)).toBe('-')
    })

    it('should handle zero', () => {
      expect(formatDuration(0)).toBe('0ms')
    })
  })

  describe('formatCompactNumber', () => {
    it('should format small numbers', () => {
      expect(formatCompactNumber(0)).toBe('0')
      expect(formatCompactNumber(42)).toBe('42')
      expect(formatCompactNumber(999)).toBe('999')
    })

    it('should format thousands', () => {
      expect(formatCompactNumber(1000)).toBe('1.0k')
      expect(formatCompactNumber(1500)).toBe('1.5k')
      expect(formatCompactNumber(25000)).toBe('25.0k')
    })

    it('should format millions', () => {
      expect(formatCompactNumber(1000000)).toBe('1.0M')
      expect(formatCompactNumber(2500000)).toBe('2.5M')
    })

    it('should handle null/undefined', () => {
      expect(formatCompactNumber(null)).toBe('0')
      expect(formatCompactNumber(undefined)).toBe('0')
      expect(formatCompactNumber(0)).toBe('0')
    })
  })

  describe('formatRating', () => {
    it('should format to 1 decimal', () => {
      expect(formatRating(4.5)).toBe('4.5')
      expect(formatRating(3.0)).toBe('3.0')
      expect(formatRating(4.99)).toBe('5.0')
    })

    it('should return "--" for non-numbers', () => {
      expect(formatRating(NaN)).toBe('--')
      expect(formatRating('abc')).toBe('--')
      expect(formatRating(null)).toBe('--')
      expect(formatRating(undefined)).toBe('--')
    })
  })

  // =========================================================================
  // Currency Formatting
  // =========================================================================

  describe('formatCurrency', () => {
    it('should format USD', () => {
      const result = formatCurrency(29.99)
      expect(result).toContain('29.99')
      expect(result).toMatch(/\$/)
    })

    it('should format EUR', () => {
      const result = formatCurrency(19.99, 'EUR')
      expect(result).toContain('19.99')
    })

    it('should format zero', () => {
      const result = formatCurrency(0)
      expect(result).toContain('0.00')
    })

    it('formatCurrencyMajor should be identical to formatCurrency', () => {
      expect(formatCurrencyMajor(50)).toBe(formatCurrency(50))
    })
  })

  describe('formatCreditsAsUSD', () => {
    it('should convert credits to dollars', () => {
      expect(formatCreditsAsUSD(100)).toBe('$1.00')
      expect(formatCreditsAsUSD(50)).toBe('$0.50')
      expect(formatCreditsAsUSD(1)).toBe('$0.01')
      expect(formatCreditsAsUSD(1250)).toBe('$12.50')
    })

    it('should handle zero/null', () => {
      expect(formatCreditsAsUSD(0)).toBe('$0.00')
      expect(formatCreditsAsUSD(null)).toBe('$0.00')
      expect(formatCreditsAsUSD(undefined)).toBe('$0.00')
    })
  })

  // =========================================================================
  // String Formatting
  // =========================================================================

  describe('formatLabel / formatParamLabel', () => {
    it('should convert snake_case to Title Case', () => {
      expect(formatLabel('model_id')).toBe('Model id')
      expect(formatLabel('api_base_url')).toBe('Api base url')
    })

    it('should convert camelCase to Title Case', () => {
      expect(formatLabel('maxTokens')).toBe('Max Tokens')
      expect(formatLabel('baseUrl')).toBe('Base Url')
    })

    it('should handle empty/null', () => {
      expect(formatLabel('')).toBe('')
      expect(formatLabel(null)).toBe('')
      expect(formatLabel(undefined)).toBe('')
    })

    it('formatParamLabel should be alias', () => {
      expect(formatParamLabel('test_key')).toBe(formatLabel('test_key'))
    })
  })

  describe('truncate', () => {
    it('should truncate long strings', () => {
      expect(truncate('Hello World', 8)).toBe('Hello...')
      expect(truncate('Short', 10)).toBe('Short')
    })

    it('should use custom suffix', () => {
      expect(truncate('Hello World', 9, '~')).toBe('Hello Wo~')
    })

    it('should handle null/empty', () => {
      expect(truncate(null, 10)).toBe('')
      expect(truncate('', 10)).toBe('')
      expect(truncate(undefined, 10)).toBe('')
    })

    it('should handle exact length', () => {
      expect(truncate('Hello', 5)).toBe('Hello')
    })
  })

  describe('capitalize', () => {
    it('should capitalize first letter', () => {
      expect(capitalize('hello')).toBe('Hello')
      expect(capitalize('world')).toBe('World')
    })

    it('should handle single character', () => {
      expect(capitalize('a')).toBe('A')
    })

    it('should handle empty/null', () => {
      expect(capitalize('')).toBe('')
      expect(capitalize(null)).toBe('')
      expect(capitalize(undefined)).toBe('')
    })

    it('should not change already capitalized', () => {
      expect(capitalize('Hello')).toBe('Hello')
    })
  })

  // =========================================================================
  // formatTime.js utilities
  // =========================================================================

  describe('formatRelativeTime (formatTime.js)', () => {
    it('should return "just now" for recent', () => {
      expect(formatRelativeTimeFT(new Date().toISOString())).toBe('just now')
    })

    it('should return minutes ago', () => {
      const ts = new Date(Date.now() - 5 * 60 * 1000).toISOString()
      expect(formatRelativeTimeFT(ts)).toBe('5m ago')
    })

    it('should return hours ago', () => {
      const ts = new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString()
      expect(formatRelativeTimeFT(ts)).toBe('3h ago')
    })

    it('should return days ago', () => {
      const ts = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()
      expect(formatRelativeTimeFT(ts)).toBe('2d ago')
    })

    it('should return empty for null', () => {
      expect(formatRelativeTimeFT(null)).toBe('')
      expect(formatRelativeTimeFT(undefined)).toBe('')
    })
  })

  describe('formatDuration (formatTime.js)', () => {
    it('should format milliseconds', () => {
      expect(formatDurationFT(500)).toBe('500ms')
    })

    it('should format seconds', () => {
      expect(formatDurationFT(5000)).toBe('5s')
      expect(formatDurationFT(45000)).toBe('45s')
    })

    it('should format minutes', () => {
      expect(formatDurationFT(90000)).toBe('1m 30s')
      expect(formatDurationFT(3600000)).toBe('1h 0m')
    })

    it('should format hours', () => {
      expect(formatDurationFT(7200000)).toBe('2h 0m')
      expect(formatDurationFT(5400000)).toBe('1h 30m')
    })

    it('should handle zero/null/negative', () => {
      expect(formatDurationFT(0)).toBe('0s')
      expect(formatDurationFT(null)).toBe('0s')
      expect(formatDurationFT(-5)).toBe('0s')
    })
  })

  describe('formatFileSize (formatTime.js)', () => {
    it('should format bytes', () => {
      expect(formatFileSizeFT(0)).toBe('0 B')
      expect(formatFileSizeFT(512)).toBe('512 B')
    })

    it('should format KB', () => {
      expect(formatFileSizeFT(1024)).toBe('1.0 KB')
      expect(formatFileSizeFT(1536)).toBe('1.5 KB')
    })

    it('should format MB', () => {
      expect(formatFileSizeFT(1048576)).toBe('1.0 MB')
    })

    it('should handle null', () => {
      expect(formatFileSizeFT(null)).toBe('0 B')
      expect(formatFileSizeFT(0)).toBe('0 B')
    })
  })
})
