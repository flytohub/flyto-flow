import { describe, it, expect } from 'vitest'
import { formatRelativeTime, formatDuration, formatFileSize } from '@/utils/formatTime'

describe('formatTime utilities', () => {
  describe('formatRelativeTime', () => {
    it('returns empty string for falsy input', () => {
      expect(formatRelativeTime(null)).toBe('')
      expect(formatRelativeTime(undefined)).toBe('')
      expect(formatRelativeTime('')).toBe('')
    })

    it('returns "just now" for very recent timestamps', () => {
      expect(formatRelativeTime(new Date().toISOString())).toBe('just now')
    })

    it('returns minutes ago', () => {
      const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString()
      expect(formatRelativeTime(fiveMinAgo)).toBe('5m ago')
    })

    it('returns hours ago', () => {
      const threeHoursAgo = new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString()
      expect(formatRelativeTime(threeHoursAgo)).toBe('3h ago')
    })

    it('returns days ago', () => {
      const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()
      expect(formatRelativeTime(twoDaysAgo)).toBe('2d ago')
    })
  })

  describe('formatDuration', () => {
    it('returns "0s" for falsy or negative input', () => {
      expect(formatDuration(0)).toBe('0s')
      expect(formatDuration(null)).toBe('0s')
      expect(formatDuration(-100)).toBe('0s')
    })

    it('formats milliseconds', () => {
      expect(formatDuration(500)).toBe('500ms')
    })

    it('formats seconds', () => {
      expect(formatDuration(5000)).toBe('5s')
      expect(formatDuration(30000)).toBe('30s')
    })

    it('formats minutes and seconds', () => {
      expect(formatDuration(90000)).toBe('1m 30s')
    })

    it('formats hours and minutes', () => {
      expect(formatDuration(3661000)).toBe('1h 1m')
    })
  })

  describe('formatFileSize', () => {
    it('returns "0 B" for 0 or falsy', () => {
      expect(formatFileSize(0)).toBe('0 B')
      expect(formatFileSize(null)).toBe('0 B')
    })

    it('formats bytes', () => {
      expect(formatFileSize(500)).toBe('500 B')
    })

    it('formats kilobytes', () => {
      expect(formatFileSize(1024)).toBe('1.0 KB')
      expect(formatFileSize(1536)).toBe('1.5 KB')
    })

    it('formats megabytes', () => {
      expect(formatFileSize(1048576)).toBe('1.0 MB')
    })
  })
})
