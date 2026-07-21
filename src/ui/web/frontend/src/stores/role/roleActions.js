/**
 * Role CRUD Actions
 *
 * S-Grade: Role CRUD operations.
 * Single responsibility: Create, read, update, delete roles.
 */

import { rolesAPI } from '@/api/roles'
import i18n from '@/i18n'
import { asObject, asRecordArray, asNonNegativeInteger } from '@/utils/dataBoundary'

/**
 * Create role CRUD actions
 * @param {Object} state - State refs
 * @returns {Object} Role action functions
 */
export function createRoleActions(state) {
  const { roles, isLoading, error, builtinCount, customCount, totalCount } = state

  /**
   * Fetch all roles
   */
  async function fetchRoles() {
    isLoading.value = true
    error.value = null

    try {
      const result = await rolesAPI.getRoles()
      const normalized = asObject(result)
      if (normalized.ok) {
        roles.value = asRecordArray(normalized.roles)
        // S-Grade: Use backend-computed counts
        if (normalized.builtinCount !== undefined || normalized.builtin_count !== undefined) {
          builtinCount.value = asNonNegativeInteger(normalized.builtinCount ?? normalized.builtin_count, 0)
        }
        if (normalized.customCount !== undefined || normalized.custom_count !== undefined) {
          customCount.value = asNonNegativeInteger(normalized.customCount ?? normalized.custom_count, 0)
        }
        if (normalized.totalCount !== undefined || normalized.total_count !== undefined) {
          totalCount.value = asNonNegativeInteger(normalized.totalCount ?? normalized.total_count, roles.value.length)
        }
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchRoles')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create new role
   */
  async function createRole(data) {
    isLoading.value = true
    error.value = null

    try {
      const result = await rolesAPI.create(data)
      const normalized = asObject(result)
      const role = asObject(normalized.role)
      if (normalized.ok && Object.keys(role).length > 0) {
        roles.value.push(role)
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToCreateRole')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update role
   */
  async function updateRole(roleId, data) {
    isLoading.value = true
    error.value = null

    try {
      const result = await rolesAPI.update(roleId, data)
      const normalized = asObject(result)
      if (normalized.ok) {
        const index = roles.value.findIndex(r => r?.id === roleId)
        if (index !== -1) {
          roles.value[index] = { ...roles.value[index], ...data }
        }
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToUpdateRole')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete role
   */
  async function deleteRole(roleId) {
    isLoading.value = true
    error.value = null

    try {
      const result = await rolesAPI.delete(roleId)
      const normalized = asObject(result)
      if (normalized.ok) {
        roles.value = roles.value.filter(r => r?.id !== roleId)
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToDeleteRole')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  return {
    fetchRoles,
    createRole,
    updateRole,
    deleteRole,
  }
}
