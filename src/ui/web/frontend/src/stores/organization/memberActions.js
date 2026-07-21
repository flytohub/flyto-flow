/**
 * Member Actions
 *
 * S-Grade: Member management operations.
 * Single responsibility: Manage organization members and invites.
 */

import { organizationAPI } from '@/api/organization'
import i18n from '@/i18n'
import { telemetry } from '@/services/telemetry'
import { asObject, asRecordArray, asNonNegativeInteger } from '@/utils/dataBoundary'

/**
 * Create member actions
 * @param {Object} state - State refs
 * @returns {Object} Member action functions
 */
export function createMemberActions(state) {
  const {
    organization,
    members,
    pendingInvites,
    isLoadingMembers,
    error,
    memberCount,
    adminCount
  } = state

  /**
   * Fetch organization members
   */
  async function fetchMembers() {
    if (!organization.value?.id) {
      return { ok: false, error: i18n.global.t('error.noOrganizationLoaded') }
    }

    isLoadingMembers.value = true
    error.value = null

    try {
      const result = await organizationAPI.getMembers(organization.value.id)
      const normalized = asObject(result)
      if (normalized.ok) {
        members.value = asRecordArray(normalized.members)

        // S-Grade: Use backend-computed counts
        if (normalized.memberCount !== undefined || normalized.member_count !== undefined) {
          memberCount.value = asNonNegativeInteger(normalized.memberCount ?? normalized.member_count, members.value.length)
        }
        if (normalized.adminCount !== undefined || normalized.admin_count !== undefined) {
          adminCount.value = asNonNegativeInteger(normalized.adminCount ?? normalized.admin_count, 0)
        }
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchMembers')
      return { ok: false, error: error.value }
    } finally {
      isLoadingMembers.value = false
    }
  }

  /**
   * Update member role
   */
  async function updateMemberRole(userId, role) {
    if (!organization.value?.id) {
      return { ok: false, error: i18n.global.t('error.noOrganizationLoaded') }
    }

    isLoadingMembers.value = true
    error.value = null

    try {
      const result = await organizationAPI.updateMember(organization.value.id, userId, { role })
      const normalized = asObject(result)
      if (normalized.ok) {
        telemetry.track('organization.member_role_update', {
          orgId: organization.value.id,
          newRole: role
        })
        const index = members.value.findIndex(m => m?.userId === userId)
        if (index !== -1) {
          members.value[index].role = role
        }
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToUpdateMember')
      return { ok: false, error: error.value }
    } finally {
      isLoadingMembers.value = false
    }
  }

  /**
   * Remove member from organization
   */
  async function removeMember(userId) {
    if (!organization.value?.id) {
      return { ok: false, error: i18n.global.t('error.noOrganizationLoaded') }
    }

    isLoadingMembers.value = true
    error.value = null

    try {
      const result = await organizationAPI.removeMember(organization.value.id, userId)
      const normalized = asObject(result)
      if (normalized.ok) {
        telemetry.track('organization.member_remove', {
          orgId: organization.value.id
        })
        members.value = members.value.filter(m => m?.userId !== userId)
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToRemoveMember')
      return { ok: false, error: error.value }
    } finally {
      isLoadingMembers.value = false
    }
  }

  /**
   * Invite new member
   */
  async function inviteMember(data) {
    if (!organization.value?.id) {
      return { ok: false, error: i18n.global.t('error.noOrganizationLoaded') }
    }

    isLoadingMembers.value = true
    error.value = null

    try {
      const result = await organizationAPI.invite(organization.value.id, data)
      const normalized = asObject(result)
      const invite = asObject(normalized.invite)
      if (normalized.ok && Object.keys(invite).length > 0) {
        telemetry.track('organization.member_invite', {
          orgId: organization.value.id,
          role: data.role
        })
        pendingInvites.value.push(invite)
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToInviteMember')
      return { ok: false, error: error.value }
    } finally {
      isLoadingMembers.value = false
    }
  }

  return {
    fetchMembers,
    updateMemberRole,
    removeMember,
    inviteMember,
  }
}

/**
 * Create utility actions
 * @param {Object} state - State refs
 * @returns {Object} Utility action functions
 */
export function createUtilityActions(state) {
  const {
    organization,
    members,
    pendingInvites,
    isLoading,
    isLoadingMembers,
    error,
    memberCount,
    adminCount
  } = state

  /**
   * Clear error
   */
  function clearError() {
    error.value = null
  }

  /**
   * Reset state
   */
  function reset() {
    organization.value = null
    members.value = []
    pendingInvites.value = []
    // S-Grade: Reset backend-computed counts
    memberCount.value = 0
    adminCount.value = 0
    isLoading.value = false
    isLoadingMembers.value = false
    error.value = null
  }

  return {
    clearError,
    reset,
  }
}
