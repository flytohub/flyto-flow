/**
 * Issues API - Public issue tracking (GitHub Issues style)
 */

import { get, post, put, del } from '@/api/client'
import { ENDPOINTS } from '@/api/config'

export const IssueType = {
  BUG: 'bug',
  FEATURE: 'feature',
  QUESTION: 'question'
}

export const IssueStatus = {
  OPEN: 'open',
  IN_PROGRESS: 'in_progress',
  CLOSED: 'closed'
}

export const IssuePriority = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high'
}

export const issuesAPI = {
  /**
   * List issues (public)
   */
  async list({ status = null, type = null, sort = 'newest', page = 1, page_size = 20 } = {}) {
    try {
      const params = { page, page_size, sort }
      if (status) params.status = status
      if (type) params.type = type
      const result = await get(ENDPOINTS.ISSUES.LIST, { params })
      return {
        ok: true,
        issues: result.issues || [],
        total: result.total || 0,
        page: result.page || page,
        page_size: result.page_size || page_size,
        has_next: result.has_next || false,
        has_prev: result.has_prev || false,
      }
    } catch (err) {
      return { ok: false, error: err.message, issues: [], total: 0 }
    }
  },

  /**
   * Get single issue (public)
   */
  async getById(id) {
    try {
      const result = await get(ENDPOINTS.ISSUES.GET(id))
      return { ok: true, issue: result.issue }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Create an issue (requires auth)
   */
  async create(data) {
    try {
      const result = await post(ENDPOINTS.ISSUES.CREATE, data)
      return { ok: true, issue: result.issue }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Update an issue (author or admin)
   */
  async update(id, data) {
    try {
      const result = await put(ENDPOINTS.ISSUES.UPDATE(id), data)
      return { ok: true, issue: result.issue }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Delete an issue (admin only)
   */
  async delete(id) {
    try {
      await del(ENDPOINTS.ISSUES.DELETE(id))
      return { ok: true }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Toggle upvote (requires auth)
   */
  async toggleUpvote(id) {
    try {
      const result = await post(ENDPOINTS.ISSUES.UPVOTE(id))
      return { ok: true, issue: result.issue }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * List comments (public)
   */
  async listComments(issueId, { page = 1, page_size = 50 } = {}) {
    try {
      const result = await get(ENDPOINTS.ISSUES.COMMENTS(issueId), {
        params: { page, page_size }
      })
      return {
        ok: true,
        comments: result.comments || [],
        total: result.total || 0,
      }
    } catch (err) {
      return { ok: false, error: err.message, comments: [], total: 0 }
    }
  },

  /**
   * Create a comment (requires auth)
   */
  async createComment(issueId, data) {
    try {
      const result = await post(ENDPOINTS.ISSUES.COMMENTS(issueId), data)
      return { ok: true, comment: result.comment }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Delete a comment (author or admin)
   */
  async deleteComment(issueId, commentId) {
    try {
      await del(ENDPOINTS.ISSUES.DELETE_COMMENT(issueId, commentId))
      return { ok: true }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },
}

export default issuesAPI
