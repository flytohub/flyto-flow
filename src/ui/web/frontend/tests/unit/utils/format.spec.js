import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock i18n
vi.mock('@/i18n', () => ({
  getLocale: vi.fn(() => 'en-US')
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
  formatCreditsAsUSD,
  formatLabel,
  formatParamLabel,
  truncate,
  capitalize
} from '@/utils/format'

describe('format utilities', () => {
  describe('formatDate', () => {
    it('returns "-" for falsy input', () => {
      expect(formatDate(null)).toBe('-')
      expect(formatDate(undefined)).toBe('-')
      expect(formatDate('')).toBe('-')
    })

    it('returns "-" for invalid date', () => {
      expect(formatDate('not-a-date')).toBe('-')
    })

    it('formats a valid Date object', () => {
      const result = formatDate(new Date('2025-01-15'))
      expect(typeof result).toBe('string')
      expect(result).not.toBe('-')
    })

    it('formats a timestamp number', () => {
      const result = formatDate(1705276800000)
      expect(typeof result).toBe('string')
      expect(result).not.toBe('-')
    })

    it('formats a date string', () => {
      const result = formatDate('2025-06-15')
      expect(typeof result).toBe('string')
      expect(result).not.toBe('-')
    })
  })

  describe('formatDateTime', () => {
    it('returns "-" for falsy input', () => {
      expect(formatDateTime(null)).toBe('-')
    })

    it('returns a string with time components for valid date', () => {
      const result = formatDateTime(new Date('2025-01-15T14:30:00'))
      expect(typeof result).toBe('string')
      expect(result).not.toBe('-')
    })
  })

  describe('formatTime', () => {
    it('returns empty string for falsy input', () => {
      expect(formatTime(null)).toBe('')
      expect(formatTime(undefined)).toBe('')
      expect(formatTime('')).toBe('')
    })

    it('returns empty string for invalid date', () => {
      expect(formatTime('invalid')).toBe('')
    })

    it('formats a valid date to time string', () => {
      const result = formatTime(new Date('2025-01-15T14:30:45'))
      expect(typeof result).toBe('string')
      expect(result).not.toBe('')
    })
  })

  describe('formatRelativeTime', () => {
    it('returns "-" for falsy input', () => {
      expect(formatRelativeTime(null)).toBe('-')
      expect(formatRelativeTime(undefined)).toBe('-')
    })

    it('returns "-" for invalid date', () => {
      expect(formatRelativeTime('not-a-date')).toBe('-')
    })

    it('returns "just now" for very recent dates', () => {
      const now = new Date()
      expect(formatRelativeTime(now)).toBe('just now')
    })

    it('returns minutes ago for recent dates', () => {
      const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000)
      expect(formatRelativeTime(fiveMinAgo)).toBe('5m ago')
    })

    it('returns hours ago', () => {
      const threeHoursAgo = new Date(Date.now() - 3 * 60 * 60 * 1000)
      expect(formatRelativeTime(threeHoursAgo)).toBe('3h ago')
    })

    it('returns days ago', () => {
      const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000)
      expect(formatRelativeTime(twoDaysAgo)).toBe('2d ago')
    })

    it('returns weeks ago', () => {
      const twoWeeksAgo = new Date(Date.now() - 14 * 24 * 60 * 60 * 1000)
      expect(formatRelativeTime(twoWeeksAgo)).toBe('2w ago')
    })
  })

  describe('formatNumber', () => {
    it('returns "0" for non-number input', () => {
      expect(formatNumber(null)).toBe('0')
      expect(formatNumber(undefined)).toBe('0')
      expect(formatNumber('abc')).toBe('0')
      expect(formatNumber(NaN)).toBe('0')
    })

    it('formats a valid number', () => {
      const result = formatNumber(1234.56)
      expect(typeof result).toBe('string')
      expect(result).toContain('1')
    })
  })

  describe('formatPercent', () => {
    it('returns "0%" for non-number input', () => {
      expect(formatPercent(null)).toBe('0%')
      expect(formatPercent(undefined)).toBe('0%')
      expect(formatPercent(NaN)).toBe('0%')
    })

    it('formats percentage from integer value', () => {
      expect(formatPercent(75)).toBe('75.0%')
      expect(formatPercent(100)).toBe('100.0%')
    })

    it('formats percentage from decimal value', () => {
      expect(formatPercent(0.75, { isDecimal: true })).toBe('75.0%')
    })

    it('respects decimal places option', () => {
      expect(formatPercent(33.333, { decimals: 2 })).toBe('33.33%')
    })
  })

  describe('formatBytes', () => {
    it('returns "0 Bytes" for 0 or falsy', () => {
      expect(formatBytes(0)).toBe('0 Bytes')
      expect(formatBytes(null)).toBe('0 Bytes')
      expect(formatBytes(undefined)).toBe('0 Bytes')
    })

    it('formats bytes', () => {
      expect(formatBytes(500)).toBe('500 Bytes')
    })

    it('formats kilobytes', () => {
      expect(formatBytes(1024)).toBe('1 KB')
    })

    it('formats megabytes', () => {
      expect(formatBytes(1048576)).toBe('1 MB')
    })

    it('formats gigabytes', () => {
      expect(formatBytes(1073741824)).toBe('1 GB')
    })

    it('respects decimal places', () => {
      expect(formatBytes(1536, 1)).toBe('1.5 KB')
    })
  })

  describe('formatFileSize (alias)', () => {
    it('is the same function as formatBytes', () => {
      expect(formatFileSize).toBe(formatBytes)
    })
  })

  describe('formatDuration', () => {
    it('returns "-" for null/undefined/NaN', () => {
      expect(formatDuration(null)).toBe('-')
      expect(formatDuration(undefined)).toBe('-')
      expect(formatDuration(NaN)).toBe('-')
    })

    it('formats milliseconds', () => {
      expect(formatDuration(500)).toBe('500ms')
    })

    it('formats seconds', () => {
      expect(formatDuration(1500)).toBe('1.5s')
    })

    it('formats minutes and seconds', () => {
      expect(formatDuration(90000)).toBe('1m 30s')
    })

    it('formats minutes only when seconds are 0', () => {
      expect(formatDuration(120000)).toBe('2m')
    })

    it('formats sub-millisecond as 0ms', () => {
      expect(formatDuration(0)).toBe('0ms')
    })
  })

  describe('formatCompactNumber', () => {
    it('returns "0" for falsy input', () => {
      expect(formatCompactNumber(0)).toBe('0')
      expect(formatCompactNumber(null)).toBe('0')
    })

    it('formats thousands', () => {
      expect(formatCompactNumber(1500)).toBe('1.5k')
    })

    it('formats millions', () => {
      expect(formatCompactNumber(2500000)).toBe('2.5M')
    })

    it('returns plain number for values under 1000', () => {
      expect(formatCompactNumber(999)).toBe('999')
    })
  })

  describe('formatRating', () => {
    it('returns "--" for non-number input', () => {
      expect(formatRating(null)).toBe('--')
      expect(formatRating(undefined)).toBe('--')
      expect(formatRating('abc')).toBe('--')
      expect(formatRating(NaN)).toBe('--')
    })

    it('formats rating to 1 decimal place', () => {
      expect(formatRating(4.5)).toBe('4.5')
      expect(formatRating(3)).toBe('3.0')
      expect(formatRating(4.567)).toBe('4.6')
    })
  })

  describe('formatCurrency', () => {
    it('formats USD by default', () => {
      const result = formatCurrency(10.5)
      expect(result).toContain('10')
    })

    it('formats specified currency', () => {
      const result = formatCurrency(10, 'EUR')
      expect(typeof result).toBe('string')
    })
  })

  describe('formatCreditsAsUSD', () => {
    it('returns "$0.00" for falsy input', () => {
      expect(formatCreditsAsUSD(0)).toBe('$0.00')
      expect(formatCreditsAsUSD(null)).toBe('$0.00')
      expect(formatCreditsAsUSD(undefined)).toBe('$0.00')
    })

    it('converts credits to dollars', () => {
      expect(formatCreditsAsUSD(100)).toBe('$1.00')
      expect(formatCreditsAsUSD(50)).toBe('$0.50')
      expect(formatCreditsAsUSD(1234)).toBe('$12.34')
    })
  })

  describe('formatLabel', () => {
    it('returns empty string for falsy input', () => {
      expect(formatLabel(null)).toBe('')
      expect(formatLabel(undefined)).toBe('')
      expect(formatLabel('')).toBe('')
    })

    it('converts snake_case to Title Case', () => {
      expect(formatLabel('model_id')).toBe('Model id')
    })

    it('converts camelCase to Title Case', () => {
      expect(formatLabel('maxTokens')).toBe('Max Tokens')
    })

    it('capitalizes first letter', () => {
      expect(formatLabel('name')).toBe('Name')
    })
  })

  describe('formatParamLabel (alias)', () => {
    it('is the same function as formatLabel', () => {
      expect(formatParamLabel).toBe(formatLabel)
    })
  })

  describe('truncate', () => {
    it('returns empty string for falsy input', () => {
      expect(truncate(null, 10)).toBe('')
      expect(truncate(undefined, 10)).toBe('')
    })

    it('returns original string if under max length', () => {
      expect(truncate('hello', 10)).toBe('hello')
    })

    it('truncates with ellipsis', () => {
      expect(truncate('hello world', 8)).toBe('hello...')
    })

    it('uses custom suffix', () => {
      expect(truncate('hello world', 8, '~')).toBe('hello w~')
    })

    it('returns original when exactly at max length', () => {
      expect(truncate('hello', 5)).toBe('hello')
    })
  })

  describe('capitalize', () => {
    it('returns empty string for falsy input', () => {
      expect(capitalize(null)).toBe('')
      expect(capitalize(undefined)).toBe('')
      expect(capitalize('')).toBe('')
    })

    it('capitalizes first letter', () => {
      expect(capitalize('hello')).toBe('Hello')
    })

    it('does not change already capitalized string', () => {
      expect(capitalize('Hello')).toBe('Hello')
    })

    it('handles single character', () => {
      expect(capitalize('a')).toBe('A')
    })
  })
})
