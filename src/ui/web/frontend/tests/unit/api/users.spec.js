import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/client', () => ({
  get: vi.fn(),
  post: vi.fn(),
  del: vi.fn()
}))

vi.mock('@/api/config', () => ({
  ENDPOINTS: {
    USERS: {
      GET: (id) => `/users/${id}`,
      FOLLOW: (id) => `/users/${id}/follow`
    },
    TEMPLATES: {
      LIST: '/templates/'
    },
    NOTIFICATIONS: {
      LIST: '/notifications',
      GET: (id) => `/notifications/${id}`
    }
  }
}))

vi.mock('@/config/defaults', () => ({
  DEFAULTS: {
    PAGINATION: { DEFAULT: 20 }
  }
}))

vi.mock('@/i18n', () => ({
  default: {
    global: {
      t: vi.fn((key) => key)
    }
  }
}))

vi.mock('@/api/auth', () => ({
  authAPI: {
    getLocalUser: vi.fn(() => ({ id: 'current-user' }))
  }
}))

vi.mock('@/utils/auth', () => ({
  getCurrentUserId: vi.fn(() => 'current-user')
}))

import { get, post, del } from '@/api/client'
import {
  getUserProfile,
  getUserTemplates,
  followUser,
  unfollowUser,
  getFollowers,
  getFollowing,
  getNotifications,
  deleteNotification
} from '@/api/users'

describe('Users API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // =========================================================================
  // getUserProfile
  // =========================================================================

  describe('getUserProfile()', () => {
    it('calls GET /users/:id/profile', async () => {
      get.mockImplementation((url) => {
        if (url.includes('/profile')) {
          return Promise.resolve({ id: 'u1', email: 'u@flyto2.com', displayName: 'User' })
        }
        // Follow status check
        return Promise.resolve({ isFollowing: false })
      })

      const result = await getUserProfile('u1')

      expect(get).toHaveBeenCalledWith('/users/u1/profile')
      expect(result.id).toBe('u1')
      expect(result.displayName).toBe('User')
    })

    it('checks follow status for non-self users', async () => {
      get.mockImplementation((url) => {
        if (url.includes('/profile')) return Promise.resolve({ id: 'other-user' })
        if (url.includes('/status')) return Promise.resolve({ isFollowing: true })
        return Promise.resolve({})
      })

      const result = await getUserProfile('other-user')

      expect(get).toHaveBeenCalledWith('/users/follow/other-user/status')
      expect(result.isFollowing).toBe(true)
    })

    it('skips follow status check for self', async () => {
      get.mockResolvedValue({ id: 'current-user' })

      await getUserProfile('current-user')

      // Should not call follow status endpoint
      const followStatusCalls = get.mock.calls.filter(c => c[0].includes('/status'))
      expect(followStatusCalls).toHaveLength(0)
    })
  })

  // =========================================================================
  // getUserTemplates
  // =========================================================================

  describe('getUserTemplates()', () => {
    it('calls GET /templates/ with creatorId and visibility params', async () => {
      get.mockResolvedValue({ templates: [{ id: 't1' }], total: 1 })

      const result = await getUserTemplates('u1')

      expect(get).toHaveBeenCalledWith('/templates/', {
        params: {
          creatorId: 'u1',
          visibility: 'public',
          page: 1,
          pageSize: 20
        }
      })
      expect(result.templates).toHaveLength(1)
    })

    it('passes custom page and pageSize', async () => {
      get.mockResolvedValue({ items: [], total: 0 })

      await getUserTemplates('u1', 2, 50)

      const params = get.mock.calls[0][1].params
      expect(params.page).toBe(2)
      expect(params.pageSize).toBe(50)
    })
  })

  // =========================================================================
  // followUser / unfollowUser
  // =========================================================================

  describe('followUser()', () => {
    it('calls POST /users/:id/follow', async () => {
      post.mockResolvedValue({})

      const result = await followUser('other-user')

      expect(post).toHaveBeenCalledWith('/users/other-user/follow')
      expect(result.ok).toBe(true)
    })

    it('throws when trying to follow self', async () => {
      await expect(followUser('current-user')).rejects.toThrow()
      expect(post).not.toHaveBeenCalled()
    })
  })

  describe('unfollowUser()', () => {
    it('calls DELETE /users/:id/follow', async () => {
      del.mockResolvedValue({})

      const result = await unfollowUser('other-user')

      expect(del).toHaveBeenCalledWith('/users/other-user/follow')
      expect(result.ok).toBe(true)
    })
  })

  // =========================================================================
  // getFollowers / getFollowing
  // =========================================================================

  describe('getFollowers()', () => {
    it('calls GET /users/:id/followers with pagination', async () => {
      get.mockResolvedValue({ items: [{ id: 'u2' }], total: 1 })

      const result = await getFollowers('u1', 1, 20)

      expect(get).toHaveBeenCalledWith('/users/u1/followers', {
        params: { page: 1, pageSize: 20 }
      })
      expect(result.followers).toHaveLength(1)
      expect(result.total).toBe(1)
    })
  })

  describe('getFollowing()', () => {
    it('calls GET /users/:id/following with pagination', async () => {
      get.mockResolvedValue({ items: [{ id: 'u3' }], total: 1 })

      const result = await getFollowing('u1')

      expect(get).toHaveBeenCalledWith('/users/u1/following', {
        params: { page: 1, pageSize: 20 }
      })
      expect(result.following).toHaveLength(1)
    })
  })

  // =========================================================================
  // getNotifications / deleteNotification
  // =========================================================================

  describe('getNotifications()', () => {
    it('calls GET /notifications with pagination and unreadOnly', async () => {
      get.mockResolvedValue({ items: [], total: 0 })

      await getNotifications(1, 20, true)

      expect(get).toHaveBeenCalledWith('/notifications', {
        params: { page: 1, pageSize: 20, unreadOnly: true }
      })
    })
  })

  describe('deleteNotification()', () => {
    it('calls DELETE /notifications/:id', async () => {
      del.mockResolvedValue({})

      const result = await deleteNotification('notif-1')

      expect(del).toHaveBeenCalledWith('/notifications/notif-1')
      expect(result.ok).toBe(true)
    })
  })
})
