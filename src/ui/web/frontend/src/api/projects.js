/**
 * Projects API - Phase 7 Multi-tenancy
 * Project management endpoints
 */

import { get, post, put, del } from '@/api/client'

const ENDPOINTS = {
  LIST: '/projects',
  CREATE: '/projects',
  GET: (id) => `/projects/${id}`,
  UPDATE: (id) => `/projects/${id}`,
  DELETE: (id) => `/projects/${id}`,
  MEMBERS: (id) => `/projects/${id}/members`
}

export const projectsAPI = {
  /**
   * Get all projects
   * @returns {Promise<Object>}
   */
  async getProjects() {
    try {
      const result = await get(ENDPOINTS.LIST)

      return {
        ok: true,
        projects: (result.projects || []).map(p => ({
          id: p.id,
          name: p.name,
          description: p.description,
          color: p.color,
          icon: p.icon,
          workflowCount: p.workflowCount || 0,
          memberCount: p.memberCount || 0,
          createdAt: p.createdAt,
          updatedAt: p.updatedAt
        }))
      }
    } catch (err) {
      return { ok: false, error: err.message, projects: [] }
    }
  },

  /**
   * Get single project
   * @param {string} projectId - Project ID
   * @returns {Promise<Object>}
   */
  async getProject(projectId) {
    try {
      const result = await get(ENDPOINTS.GET(projectId))

      return {
        ok: true,
        project: {
          id: result.id,
          name: result.name,
          description: result.description,
          color: result.color,
          icon: result.icon,
          workflowCount: result.workflowCount || 0,
          memberCount: result.memberCount || 0,
          settings: result.settings || {},
          createdAt: result.createdAt,
          updatedAt: result.updatedAt
        }
      }
    } catch (err) {
      return { ok: false, error: err.message, project: null }
    }
  },

  /**
   * Create new project
   * @param {Object} data - Project data
   * @returns {Promise<Object>}
   */
  async create(data) {
    try {
      const result = await post(ENDPOINTS.CREATE, data)

      return {
        ok: true,
        project: {
          id: result.id,
          name: result.name,
          description: result.description,
          color: result.color,
          icon: result.icon,
          workflowCount: 0,
          memberCount: 1,
          createdAt: result.createdAt,
          updatedAt: result.updatedAt
        }
      }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Update project
   * @param {string} projectId - Project ID
   * @param {Object} data - Update data
   * @returns {Promise<Object>}
   */
  async update(projectId, data) {
    try {
      const result = await put(ENDPOINTS.UPDATE(projectId), data)
      return { ok: true, project: result }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Delete project
   * @param {string} projectId - Project ID
   * @returns {Promise<Object>}
   */
  async delete(projectId) {
    try {
      await del(ENDPOINTS.DELETE(projectId))
      return { ok: true }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Get project members
   * @param {string} projectId - Project ID
   * @returns {Promise<Object>}
   */
  async getMembers(projectId) {
    try {
      const result = await get(ENDPOINTS.MEMBERS(projectId))

      return {
        ok: true,
        members: (result.members || []).map(m => ({
          userId: m.userId,
          email: m.email,
          name: m.name,
          avatarUrl: m.avatarUrl,
          role: m.role || 'member',
          joinedAt: m.joinedAt
        }))
      }
    } catch (err) {
      return { ok: false, error: err.message, members: [] }
    }
  }
}

export default projectsAPI
