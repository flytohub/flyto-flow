import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock dependencies
vi.mock('@/api/auth', () => ({
  authAPI: {
    getLocalUser: vi.fn(),
    waitForAuth: vi.fn()
  }
}))

vi.mock('@/i18n', () => ({
  default: {
    global: {
      t: vi.fn((key) => key)
    }
  }
}))

import { getCurrentUserId, getCurrentUser, waitForAuthAndGetUserId } from '@/utils/auth'
import { authAPI } from '@/api/auth'

describe('auth utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getCurrentUserId', () => {
    it('returns user.id when available', () => {
      authAPI.getLocalUser.mockReturnValue({ id: 'user-123', uid: 'uid-456' })
      expect(getCurrentUserId()).toBe('user-123')
    })

    it('falls back to user.uid', () => {
      authAPI.getLocalUser.mockReturnValue({ uid: 'uid-456' })
      expect(getCurrentUserId()).toBe('uid-456')
    })

    it('throws when not authenticated', () => {
      authAPI.getLocalUser.mockReturnValue(null)
      expect(() => getCurrentUserId()).toThrow()
    })
  })

  describe('getCurrentUser', () => {
    it('returns structured user object', () => {
      authAPI.getLocalUser.mockReturnValue({
        id: 'user-123',
        email: 'test@flyto2.com',
        displayName: 'Test User'
      })

      const user = getCurrentUser()
      expect(user).toEqual({
        uid: 'user-123',
        email: 'test@flyto2.com',
        displayName: 'Test User'
      })
    })

    it('falls back displayName through multiple fields', () => {
      authAPI.getLocalUser.mockReturnValue({
        uid: 'uid-1',
        email: 'test@flyto2.com'
      })
      const user = getCurrentUser()
      expect(user.displayName).toBe('test')
    })

    it('uses display_name as fallback', () => {
      authAPI.getLocalUser.mockReturnValue({
        uid: 'uid-1',
        email: 'test@flyto2.com',
        display_name: 'Display Name'
      })
      const user = getCurrentUser()
      expect(user.displayName).toBe('Display Name')
    })

    it('uses username as fallback', () => {
      authAPI.getLocalUser.mockReturnValue({
        uid: 'uid-1',
        email: 'test@flyto2.com',
        username: 'testuser'
      })
      const user = getCurrentUser()
      expect(user.displayName).toBe('testuser')
    })

    it('throws when not authenticated', () => {
      authAPI.getLocalUser.mockReturnValue(null)
      expect(() => getCurrentUser()).toThrow()
    })
  })

  describe('waitForAuthAndGetUserId', () => {
    it('returns user ID after waiting', async () => {
      authAPI.waitForAuth.mockResolvedValue({ id: 'user-123' })
      const id = await waitForAuthAndGetUserId()
      expect(id).toBe('user-123')
    })

    it('falls back to uid', async () => {
      authAPI.waitForAuth.mockResolvedValue({ uid: 'uid-456' })
      const id = await waitForAuthAndGetUserId()
      expect(id).toBe('uid-456')
    })

    it('throws when auth returns null', async () => {
      authAPI.waitForAuth.mockResolvedValue(null)
      await expect(waitForAuthAndGetUserId()).rejects.toThrow()
    })
  })
})
