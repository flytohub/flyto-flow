/**
 * Organization API - Phase 7 Multi-tenancy
 * Organization management endpoints
 */

import { get, post, put, del } from '@/api/client'

const ENDPOINTS = {
  CURRENT: '/organizations/current',
  UPDATE: (id) => `/organizations/${id}`,
  MEMBERS: (id) => `/organizations/${id}/members`,
  MEMBER: (id, uid) => `/organizations/${id}/members/${uid}`,
  INVITE: (id) => `/organizations/${id}/invite`,
  INVITATIONS: (id) => `/organizations/${id}/invitations`,
  INVITATION: (token) => `/organizations/invitations/${token}`,
  INVITATION_ACCEPT: (token) => `/organizations/invitations/${token}/accept`
}

export const organizationAPI = {
  /**
   * Get current organization
   * @returns {Promise<Object>}
   */
  async getCurrent() {
    try {
      const result = await get(ENDPOINTS.CURRENT)

      return {
        ok: true,
        organization: {
          id: result.id,
          name: result.name,
          description: result.description,
          logoUrl: result.logoUrl,
          plan: result.plan || 'free',
          createdAt: result.createdAt,
          settings: result.settings || {}
        }
      }
    } catch (err) {
      return { ok: false, error: err.message, organization: null }
    }
  },

  /**
   * Update organization
   * @param {string} orgId - Organization ID
   * @param {Object} data - Update data
   * @returns {Promise<Object>}
   */
  async update(orgId, data) {
    try {
      const result = await put(ENDPOINTS.UPDATE(orgId), data)
      return { ok: true, organization: result }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Get organization members
   * @param {string} orgId - Organization ID
   * @returns {Promise<Object>}
   */
  async getMembers(orgId) {
    try {
      const result = await get(ENDPOINTS.MEMBERS(orgId))

      return {
        ok: true,
        members: (result.members || []).map(m => ({
          userId: m.userId,
          email: m.email,
          name: m.name,
          avatarUrl: m.avatarUrl,
          role: m.role || 'member',
          joinedAt: m.joinedAt,
          lastActive: m.lastActive
        }))
      }
    } catch (err) {
      return { ok: false, error: err.message, members: [] }
    }
  },

  /**
   * Update member
   * @param {string} orgId - Organization ID
   * @param {string} userId - User ID
   * @param {Object} data - Update data (role)
   * @returns {Promise<Object>}
   */
  async updateMember(orgId, userId, data) {
    try {
      const result = await put(ENDPOINTS.MEMBER(orgId, userId), data)
      return { ok: true, member: result }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Remove member from organization
   * @param {string} orgId - Organization ID
   * @param {string} userId - User ID
   * @returns {Promise<Object>}
   */
  async removeMember(orgId, userId) {
    try {
      await del(ENDPOINTS.MEMBER(orgId, userId))
      return { ok: true }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Invite new member
   * @param {string} orgId - Organization ID
   * @param {Object} data - Invite data
   * @returns {Promise<Object>}
   */
  async invite(orgId, data) {
    try {
      const result = await post(ENDPOINTS.INVITE(orgId), data)
      return {
        ok: true,
        invite: {
          id: result.id,
          email: result.email,
          role: result.role,
          status: result.status || 'pending',
          // Backend returns snake_case expires_at / invite_url
          expiresAt: result.expires_at || result.expiresAt,
          inviteUrl: result.invite_url || result.inviteUrl
        }
      }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * List pending/historical invitations for an organization (admin only)
   * @param {string} orgId - Organization ID
   * @returns {Promise<Object>}
   */
  async listInvitations(orgId) {
    try {
      const result = await get(ENDPOINTS.INVITATIONS(orgId))
      return {
        ok: true,
        invitations: (result.invitations || []).map(inv => ({
          id: inv.id,
          email: inv.email,
          role: inv.role,
          status: inv.status,
          expiresAt: inv.expires_at,
          createdAt: inv.created_at
        })),
        pendingCount: result.pending_count || 0
      }
    } catch (err) {
      return { ok: false, error: err.message, invitations: [] }
    }
  },

  /**
   * Resolve (preview) an invitation token before accepting
   * @param {string} token - Invitation token from the invite URL
   * @returns {Promise<Object>}
   */
  async resolveInvitation(token) {
    try {
      const result = await get(ENDPOINTS.INVITATION(token))
      return {
        ok: true,
        invitation: {
          id: result.id,
          email: result.email,
          role: result.role,
          status: result.status,
          expiresAt: result.expires_at,
          organizationId: result.organization_id,
          organizationName: result.organization_name,
          valid: result.valid
        }
      }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Accept (redeem) an invitation token, joining the organization
   * @param {string} token - Invitation token from the invite URL
   * @returns {Promise<Object>}
   */
  async acceptInvitation(token) {
    try {
      const result = await post(ENDPOINTS.INVITATION_ACCEPT(token))
      return {
        ok: true,
        organizationId: result.organization_id,
        role: result.role,
        member: result.member
      }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }
}

export default organizationAPI
