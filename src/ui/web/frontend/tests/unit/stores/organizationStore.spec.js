import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/organization', () => ({
  organizationAPI: {
    getCurrent: vi.fn(),
    update: vi.fn(),
    getMembers: vi.fn(),
    updateMember: vi.fn(),
    removeMember: vi.fn(),
    invite: vi.fn(),
  }
}))

vi.mock('@/i18n', () => ({
  default: { global: { t: (key) => key } }
}))

vi.mock('@/services/telemetry', () => ({
  telemetry: { track: vi.fn() }
}))

import { useOrganizationStore } from '@/stores/organization/organizationStoreCore'
import { organizationAPI } from '@/api/organization'

describe('useOrganizationStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useOrganizationStore()
    vi.clearAllMocks()
  })

  // ==========================================================================
  // Initial State
  // ==========================================================================
  describe('initial state', () => {
    it('has correct defaults', () => {
      expect(store.organization).toBeNull()
      expect(store.members).toEqual([])
      expect(store.pendingInvites).toEqual([])
      expect(store.isLoading).toBe(false)
      expect(store.isLoadingMembers).toBe(false)
      expect(store.error).toBeNull()
      expect(store.memberCount).toBe(0)
      expect(store.adminCount).toBe(0)
    })
  })

  // ==========================================================================
  // Getters
  // ==========================================================================
  describe('getters', () => {
    it('hasOrganization returns false when null', () => {
      expect(store.hasOrganization).toBe(false)
    })

    it('hasOrganization returns true when set', () => {
      store.organization = { id: 'org-1', name: 'Test Org' }
      expect(store.hasOrganization).toBe(true)
    })
  })

  // ==========================================================================
  // fetchOrganization
  // ==========================================================================
  describe('fetchOrganization', () => {
    it('sets organization on success', async () => {
      const mockOrg = { id: 'org-1', name: 'My Org' }
      organizationAPI.getCurrent.mockResolvedValue({ ok: true, organization: mockOrg })

      const result = await store.fetchOrganization()

      expect(result.ok).toBe(true)
      expect(store.organization).toEqual(mockOrg)
      expect(store.isLoading).toBe(false)
    })

    it('sets error when API returns error', async () => {
      organizationAPI.getCurrent.mockResolvedValue({ ok: false, error: 'Not authorized' })

      await store.fetchOrganization()

      expect(store.error).toBe('Not authorized')
    })

    it('sets error on exception', async () => {
      organizationAPI.getCurrent.mockRejectedValue(new Error('Network error'))

      const result = await store.fetchOrganization()

      expect(result.ok).toBe(false)
      expect(store.error).toBe('Network error')
    })
  })

  // ==========================================================================
  // updateOrganization
  // ==========================================================================
  describe('updateOrganization', () => {
    it('merges update data on success', async () => {
      store.organization = { id: 'org-1', name: 'Old Name', plan: 'free' }
      organizationAPI.update.mockResolvedValue({ ok: true })

      const result = await store.updateOrganization({ name: 'New Name' })

      expect(result.ok).toBe(true)
      expect(store.organization.name).toBe('New Name')
      expect(store.organization.plan).toBe('free') // preserved
    })

    it('returns error when no organization loaded', async () => {
      store.organization = null

      const result = await store.updateOrganization({ name: 'test' })

      expect(result.ok).toBe(false)
    })

    it('sets error when API returns error', async () => {
      store.organization = { id: 'org-1' }
      organizationAPI.update.mockResolvedValue({ ok: false, error: 'Forbidden' })

      await store.updateOrganization({ name: 'test' })

      expect(store.error).toBe('Forbidden')
    })

    it('sets error on exception', async () => {
      store.organization = { id: 'org-1' }
      organizationAPI.update.mockRejectedValue(new Error('Timeout'))

      const result = await store.updateOrganization({ name: 'test' })

      expect(result.ok).toBe(false)
      expect(store.error).toBe('Timeout')
    })
  })

  // ==========================================================================
  // fetchMembers
  // ==========================================================================
  describe('fetchMembers', () => {
    it('sets members and counts on success', async () => {
      store.organization = { id: 'org-1' }
      organizationAPI.getMembers.mockResolvedValue({
        ok: true,
        members: [
          { userId: 'u1', role: 'admin' },
          { userId: 'u2', role: 'member' }
        ],
        memberCount: 2,
        adminCount: 1
      })

      const result = await store.fetchMembers()

      expect(result.ok).toBe(true)
      expect(store.members).toHaveLength(2)
      expect(store.memberCount).toBe(2)
      expect(store.adminCount).toBe(1)
      expect(store.isLoadingMembers).toBe(false)
    })

    it('returns error when no organization loaded', async () => {
      store.organization = null

      const result = await store.fetchMembers()

      expect(result.ok).toBe(false)
    })

    it('sets error when API fails', async () => {
      store.organization = { id: 'org-1' }
      organizationAPI.getMembers.mockRejectedValue(new Error('Server error'))

      const result = await store.fetchMembers()

      expect(result.ok).toBe(false)
      expect(store.error).toBe('Server error')
    })
  })

  // ==========================================================================
  // updateMemberRole
  // ==========================================================================
  describe('updateMemberRole', () => {
    it('updates role in members list on success', async () => {
      store.organization = { id: 'org-1' }
      store.members = [
        { userId: 'u1', role: 'member' },
        { userId: 'u2', role: 'member' }
      ]
      organizationAPI.updateMember.mockResolvedValue({ ok: true })

      const result = await store.updateMemberRole('u1', 'admin')

      expect(result.ok).toBe(true)
      expect(store.members[0].role).toBe('admin')
      expect(store.members[1].role).toBe('member')
    })

    it('returns error when no org loaded', async () => {
      store.organization = null
      const result = await store.updateMemberRole('u1', 'admin')
      expect(result.ok).toBe(false)
    })
  })

  // ==========================================================================
  // removeMember
  // ==========================================================================
  describe('removeMember', () => {
    it('removes member from list on success', async () => {
      store.organization = { id: 'org-1' }
      store.members = [
        { userId: 'u1', role: 'member' },
        { userId: 'u2', role: 'admin' }
      ]
      organizationAPI.removeMember.mockResolvedValue({ ok: true })

      const result = await store.removeMember('u1')

      expect(result.ok).toBe(true)
      expect(store.members).toHaveLength(1)
      expect(store.members[0].userId).toBe('u2')
    })

    it('returns error when no org loaded', async () => {
      store.organization = null
      const result = await store.removeMember('u1')
      expect(result.ok).toBe(false)
    })
  })

  // ==========================================================================
  // inviteMember
  // ==========================================================================
  describe('inviteMember', () => {
    it('adds invite to pendingInvites on success', async () => {
      store.organization = { id: 'org-1' }
      const mockInvite = { id: 'inv-1', email: 'new@flyto2.com', role: 'member' }
      organizationAPI.invite.mockResolvedValue({ ok: true, invite: mockInvite })

      const result = await store.inviteMember({ email: 'new@flyto2.com', role: 'member' })

      expect(result.ok).toBe(true)
      expect(store.pendingInvites).toContainEqual(mockInvite)
    })

    it('sets error when API returns error', async () => {
      store.organization = { id: 'org-1' }
      organizationAPI.invite.mockResolvedValue({ ok: false, error: 'Email already invited' })

      await store.inviteMember({ email: 'dup@flyto2.com', role: 'member' })

      expect(store.error).toBe('Email already invited')
    })

    it('returns error when no org loaded', async () => {
      store.organization = null
      const result = await store.inviteMember({ email: 'test@flyto2.com' })
      expect(result.ok).toBe(false)
    })
  })

  // ==========================================================================
  // Utility Actions
  // ==========================================================================
  describe('clearError', () => {
    it('clears the error', () => {
      store.error = 'some error'
      store.clearError()
      expect(store.error).toBeNull()
    })
  })

  describe('reset', () => {
    it('resets all state to defaults', () => {
      store.organization = { id: 'org-1' }
      store.members = [{ userId: 'u1' }]
      store.pendingInvites = [{ id: 'inv-1' }]
      store.memberCount = 5
      store.adminCount = 2
      store.isLoading = true
      store.error = 'err'

      store.reset()

      expect(store.organization).toBeNull()
      expect(store.members).toEqual([])
      expect(store.pendingInvites).toEqual([])
      expect(store.memberCount).toBe(0)
      expect(store.adminCount).toBe(0)
      expect(store.isLoading).toBe(false)
      expect(store.isLoadingMembers).toBe(false)
      expect(store.error).toBeNull()
    })
  })
})
