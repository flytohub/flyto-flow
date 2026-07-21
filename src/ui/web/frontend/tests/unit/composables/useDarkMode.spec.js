import { describe, it, expect, vi } from 'vitest'

vi.mock('@/services/storageService', () => ({
  localStore: {
    set: vi.fn(),
    get: vi.fn()
  }
}))

import { useDarkMode } from '@/composables/useDarkMode'

describe('useDarkMode', () => {
  it('returns the expected API', () => {
    const dm = useDarkMode()
    expect(dm).toHaveProperty('isDark')
    expect(dm).toHaveProperty('toggle')
    expect(dm).toHaveProperty('setDark')
  })

  it('isDark is always true (forced dark mode)', () => {
    const { isDark } = useDarkMode()
    expect(isDark.value).toBe(true)
  })

  it('toggle does not change isDark (always dark)', () => {
    const { isDark, toggle } = useDarkMode()
    toggle()
    expect(isDark.value).toBe(true)
  })

  it('setDark does not change isDark (always dark)', () => {
    const { isDark, setDark } = useDarkMode()
    setDark()
    expect(isDark.value).toBe(true)
  })

  it('shares state across instances (ref is module-level)', () => {
    const dm1 = useDarkMode()
    const dm2 = useDarkMode()
    expect(dm1.isDark).toBe(dm2.isDark)
  })
})
