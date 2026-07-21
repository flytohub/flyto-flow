/**
 * Roles API - Phase 7 Multi-tenancy
 * Role and permission management endpoints
 */

import { get, post, put, del } from '@/api/client'

const ENDPOINTS = {
  LIST: '/roles',
  CREATE: '/roles',
  GET: (id) => `/roles/${id}`,
  UPDATE: (id) => `/roles/${id}`,
  DELETE: (id) => `/roles/${id}`,
  PERMISSIONS: (id) => `/roles/${id}/permissions`,
  ALL_PERMISSIONS: '/permissions',
  ASSIGNMENTS: '/role-assignments'
}

export const rolesAPI = {
  /**
   * Get all roles
   * @returns {Promise<Object>}
   */
  async getRoles() {
    try {
      const result = await get(ENDPOINTS.LIST)

      return {
        ok: true,
        roles: (result.roles || []).map(r => ({
          id: r.id,
          name: r.name,
          description: r.description,
          isBuiltin: r.isBuiltin || false,
          permissions: r.permissions || [],
          userCount: r.userCount || 0,
          createdAt: r.createdAt,
          updatedAt: r.updatedAt
        })),
        // S-Grade: Backend-computed counts
        builtinCount: result.builtinCount,
        customCount: result.customCount,
        totalCount: result.totalCount
      }
    } catch (err) {
      return { ok: false, error: err.message, roles: [] }
    }
  },

  /**
   * Create new role
   * @param {Object} data - Role data
   * @returns {Promise<Object>}
   */
  async create(data) {
    try {
      const result = await post(ENDPOINTS.CREATE, data)

      return {
        ok: true,
        role: {
          id: result.id,
          name: result.name,
          description: result.description,
          isBuiltin: false,
          permissions: result.permissions || [],
          userCount: 0,
          createdAt: result.createdAt,
          updatedAt: result.updatedAt
        }
      }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Update role
   * @param {string} roleId - Role ID
   * @param {Object} data - Update data
   * @returns {Promise<Object>}
   */
  async update(roleId, data) {
    try {
      const result = await put(ENDPOINTS.UPDATE(roleId), data)
      return { ok: true, role: result }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Delete role
   * @param {string} roleId - Role ID
   * @returns {Promise<Object>}
   */
  async delete(roleId) {
    try {
      await del(ENDPOINTS.DELETE(roleId))
      return { ok: true }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Get available permissions
   * @returns {Promise<Object>}
   */
  async getPermissions() {
    try {
      const result = await get(ENDPOINTS.ALL_PERMISSIONS)

      return {
        ok: true,
        permissions: (result.permissions || []).map(p => ({
          id: p.id,
          name: p.name,
          description: p.description,
          category: p.category,
          resource: p.resource,
          action: p.action
        }))
      }
    } catch (err) {
      return { ok: false, error: err.message, permissions: [] }
    }
  },

  /**
   * Update role permissions
   * @param {string} roleId - Role ID
   * @param {Array} permissionIds - Permission IDs
   * @returns {Promise<Object>}
   */
  async updatePermissions(roleId, permissionIds) {
    try {
      await put(ENDPOINTS.PERMISSIONS(roleId), { permissions: permissionIds })
      return { ok: true }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Get role assignments
   * @returns {Promise<Object>}
   */
  async getAssignments() {
    try {
      const result = await get(ENDPOINTS.ASSIGNMENTS)

      return {
        ok: true,
        assignments: (result.assignments || []).map(a => ({
          userId: a.userId,
          userEmail: a.userEmail,
          userName: a.userName,
          roleId: a.roleId,
          roleName: a.roleName,
          assignedAt: a.assignedAt
        }))
      }
    } catch (err) {
      return { ok: false, error: err.message, assignments: [] }
    }
  }
}

export default rolesAPI
