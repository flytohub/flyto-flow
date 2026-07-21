/**
 * Permission Actions
 *
 * S-Grade: Permission and assignment operations.
 * Single responsibility: Manage permissions and role assignments.
 */

import { rolesAPI } from '@/api/roles'
import i18n from '@/i18n'

/**
 * Create permission actions
 * @param {Object} state - State refs
 * @returns {Object} Permission action functions
 */
export function createPermissionActions(state) {
  const { roles, permissions, assignments, isLoading, error } = state

  /**
   * Fetch available permissions
   */
  async function fetchPermissions() {
    isLoading.value = true
    error.value = null

    try {
      const result = await rolesAPI.getPermissions()
      if (result.ok) {
        permissions.value = result.permissions
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchPermissions')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update role permissions
   */
  async function updateRolePermissions(roleId, permissionIds) {
    isLoading.value = true
    error.value = null

    try {
      const result = await rolesAPI.updatePermissions(roleId, permissionIds)
      if (result.ok) {
        const index = roles.value.findIndex(r => r.id === roleId)
        if (index !== -1) {
          roles.value[index].permissions = permissionIds
        }
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToUpdatePermissions')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch role assignments
   */
  async function fetchAssignments() {
    isLoading.value = true
    error.value = null

    try {
      const result = await rolesAPI.getAssignments()
      if (result.ok) {
        assignments.value = result.assignments
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchAssignments')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  return {
    fetchPermissions,
    updateRolePermissions,
    fetchAssignments,
  }
}

/**
 * Create utility actions
 * @param {Object} state - State refs
 * @returns {Object} Utility action functions
 */
export function createUtilityActions(state) {
  const { roles, permissions, assignments, isLoading, error, builtinCount, customCount, totalCount } = state

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
    roles.value = []
    permissions.value = []
    assignments.value = []
    isLoading.value = false
    error.value = null
    // S-Grade: Reset backend-computed counts
    builtinCount.value = 0
    customCount.value = 0
    totalCount.value = 0
  }

  return {
    clearError,
    reset,
  }
}
