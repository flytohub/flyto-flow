import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

vi.mock('@/config/defaults', () => ({
  DEFAULTS: {
    TIMING: {
      TOAST_DURATION: 3000,
      TOAST_DURATION_ERROR: 5000
    }
  }
}))

import { useToast } from '@/composables/useToast'

describe('useToast', () => {
  let toast

  beforeEach(() => {
    vi.useFakeTimers()
    toast = useToast()
    toast.dismissAll()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns the expected API', () => {
    expect(toast).toHaveProperty('toasts')
    expect(toast).toHaveProperty('show')
    expect(toast).toHaveProperty('dismiss')
    expect(toast).toHaveProperty('dismissAll')
    expect(toast).toHaveProperty('success')
    expect(toast).toHaveProperty('error')
    expect(toast).toHaveProperty('warning')
    expect(toast).toHaveProperty('info')
  })

  it('starts with empty toasts', () => {
    expect(toast.toasts).toHaveLength(0)
  })

  describe('show', () => {
    it('adds a toast with default type "info"', () => {
      toast.show('hello')
      expect(toast.toasts).toHaveLength(1)
      expect(toast.toasts[0].message).toBe('hello')
      expect(toast.toasts[0].type).toBe('info')
    })

    it('returns a unique toast ID', () => {
      const id1 = toast.show('a')
      const id2 = toast.show('b')
      expect(id1).not.toBe(id2)
    })

    it('uses error duration for error type', () => {
      toast.show('err', 'error')
      expect(toast.toasts[0].duration).toBe(5000)
    })

    it('uses default duration for non-error types', () => {
      toast.show('msg', 'info')
      expect(toast.toasts[0].duration).toBe(3000)
    })

    it('allows custom duration', () => {
      toast.show('msg', 'info', 9999)
      expect(toast.toasts[0].duration).toBe(9999)
    })

    it('auto-dismisses after duration', () => {
      toast.show('msg', 'info', 1000)
      expect(toast.toasts).toHaveLength(1)
      vi.advanceTimersByTime(1000)
      expect(toast.toasts).toHaveLength(0)
    })

    it('does not auto-dismiss when duration is 0 (persistent)', () => {
      toast.show('persistent', 'info', 0)
      vi.advanceTimersByTime(60000)
      expect(toast.toasts).toHaveLength(1)
    })
  })

  describe('shorthand methods', () => {
    it('success creates success toast', () => {
      toast.success('ok')
      expect(toast.toasts[0].type).toBe('success')
      expect(toast.toasts[0].message).toBe('ok')
    })

    it('error creates error toast', () => {
      toast.error('fail')
      expect(toast.toasts[0].type).toBe('error')
    })

    it('warning creates warning toast', () => {
      toast.warning('watch out')
      expect(toast.toasts[0].type).toBe('warning')
    })

    it('info creates info toast', () => {
      toast.info('fyi')
      expect(toast.toasts[0].type).toBe('info')
    })
  })

  describe('dismiss', () => {
    it('removes a toast by ID', () => {
      const id = toast.show('a')
      toast.show('b')
      toast.dismiss(id)
      expect(toast.toasts).toHaveLength(1)
      expect(toast.toasts[0].message).toBe('b')
    })

    it('does nothing for unknown ID', () => {
      toast.show('a')
      toast.dismiss(99999)
      expect(toast.toasts).toHaveLength(1)
    })
  })

  describe('dismissAll', () => {
    it('removes all toasts', () => {
      toast.show('a')
      toast.show('b')
      toast.show('c')
      toast.dismissAll()
      expect(toast.toasts).toHaveLength(0)
    })
  })

  describe('singleton behavior', () => {
    it('shares state across multiple useToast() calls', () => {
      const toast2 = useToast()
      toast.show('shared')
      expect(toast2.toasts).toHaveLength(1)
      expect(toast2.toasts[0].message).toBe('shared')
    })
  })
})
