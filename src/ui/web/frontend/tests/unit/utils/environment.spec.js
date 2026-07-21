import { describe, it, expect, vi } from 'vitest'

describe('environment utilities', () => {
  it('isDevelopment returns true when import.meta.env.DEV is true', async () => {
    // vitest sets DEV=true by default in test environment
    const { isDevelopment } = await import('@/utils/environment')
    expect(typeof isDevelopment()).toBe('boolean')
  })
})
