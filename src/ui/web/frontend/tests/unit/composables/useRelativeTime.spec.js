import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const mockT = vi.fn((key, params) => {
  if (key === 'dashboardPage.recentActivity.justNow') return 'just now'
  if (key === 'dashboardPage.recentActivity.minutesAgo') return `${params.count} minutes ago`
  if (key === 'dashboardPage.recentActivity.hoursAgo') return `${params.count} hours ago`
  if (key === 'dashboardPage.recentActivity.yesterday') return 'yesterday'
  if (key === 'dashboardPage.recentActivity.daysAgo') return `${params.count} days ago`
  return key
})

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: mockT })
}))

vi.mock('@/constants/time', () => ({
  MS_PER_MINUTE: 60000,
  MS_PER_HOUR: 3600000,
  MS_PER_DAY: 86400000
}))

import { useRelativeTime } from '@/composables/useRelativeTime'

describe('useRelativeTime', () => {
  let formatRelativeTime

  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-03-21T12:00:00Z'))
    ;({ formatRelativeTime } = useRelativeTime())
    mockT.mockClear()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns empty string for falsy input', () => {
    expect(formatRelativeTime(null)).toBe('')
    expect(formatRelativeTime('')).toBe('')
    expect(formatRelativeTime(undefined)).toBe('')
  })

  it('returns "just now" for less than 1 minute ago', () => {
    const date = new Date(Date.now() - 30000).toISOString() // 30s ago
    expect(formatRelativeTime(date)).toBe('just now')
  })

  it('returns minutes ago for less than 1 hour', () => {
    const date = new Date(Date.now() - 5 * 60000).toISOString() // 5 min ago
    expect(formatRelativeTime(date)).toBe('5 minutes ago')
  })

  it('returns hours ago for less than 1 day', () => {
    const date = new Date(Date.now() - 3 * 3600000).toISOString() // 3h ago
    expect(formatRelativeTime(date)).toBe('3 hours ago')
  })

  it('returns "yesterday" for 1-2 days ago', () => {
    const date = new Date(Date.now() - 86400000 - 1000).toISOString() // just over 1 day
    expect(formatRelativeTime(date)).toBe('yesterday')
  })

  it('returns days ago for 2-7 days', () => {
    const date = new Date(Date.now() - 3 * 86400000).toISOString() // 3 days
    expect(formatRelativeTime(date)).toBe('3 days ago')
  })

  it('returns formatted date for older than 7 days', () => {
    const date = new Date(Date.now() - 10 * 86400000).toISOString()
    const result = formatRelativeTime(date)
    // Should be a locale date string, not a relative time
    expect(result).not.toBe('')
    expect(mockT).not.toHaveBeenCalledWith(
      expect.stringContaining('daysAgo'),
      expect.anything()
    )
  })
})
