/**
 * Templates API - Template Issue Operations
 */

import { get, post, put, del } from '@/api/client'

/** List issues for a template with optional filters and pagination */
export async function listIssues(templateId, { status, type, sort = 'newest', page = 1, pageSize = 20 } = {}) {
  try {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    if (type) params.append('type', type)
    params.append('sort', sort)
    params.append('page', page)
    params.append('page_size', pageSize)

    const result = await get(`/templates/${templateId}/issues?${params}`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Get a single issue by ID */
export async function getIssue(templateId, issueId) {
  try {
    const result = await get(`/templates/${templateId}/issues/${issueId}`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Create a new issue on a template */
export async function createIssue(templateId, { title, description, type = 'bug', labels = [] }) {
  try {
    const result = await post(`/templates/${templateId}/issues`, {
      title,
      description,
      type,
      labels,
    })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Update an existing issue's title, description, or labels */
export async function updateIssue(templateId, issueId, { title, description, labels }) {
  try {
    const result = await put(`/templates/${templateId}/issues/${issueId}`, {
      title,
      description,
      labels,
    })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Close an open issue */
export async function closeIssue(templateId, issueId) {
  try {
    const result = await post(`/templates/${templateId}/issues/${issueId}/close`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Reopen a previously closed issue */
export async function reopenIssue(templateId, issueId) {
  try {
    const result = await post(`/templates/${templateId}/issues/${issueId}/reopen`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Toggle upvote on an issue */
export async function toggleUpvote(templateId, issueId) {
  try {
    const result = await post(`/templates/${templateId}/issues/${issueId}/upvote`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Update the assignees list for an issue */
export async function updateAssignees(templateId, issueId, assignees) {
  try {
    const result = await post(`/templates/${templateId}/issues/${issueId}/assignees`, { assignees })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Link a pull request to an issue */
export async function linkPRToIssue(templateId, issueId, prId) {
  try {
    const result = await post(`/templates/${templateId}/issues/${issueId}/link-pr`, { pr_id: prId })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** List comments on an issue with pagination */
export async function listComments(templateId, issueId, { page = 1, pageSize = 50 } = {}) {
  try {
    const params = new URLSearchParams()
    params.append('page', page)
    params.append('page_size', pageSize)

    const result = await get(`/templates/${templateId}/issues/${issueId}/comments?${params}`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Add a comment to an issue */
export async function createComment(templateId, issueId, { content }) {
  try {
    const result = await post(`/templates/${templateId}/issues/${issueId}/comments`, {
      content,
    })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Update an existing issue comment */
export async function updateComment(templateId, issueId, commentId, { content }) {
  try {
    const result = await put(`/templates/${templateId}/issues/${issueId}/comments/${commentId}`, { content })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Delete a comment from an issue */
export async function deleteComment(templateId, issueId, commentId) {
  try {
    const result = await del(`/templates/${templateId}/issues/${issueId}/comments/${commentId}`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Toggle a reaction on an issue */
export async function toggleIssueReaction(templateId, issueId, reactionType) {
  try {
    const result = await post(`/templates/${templateId}/issues/${issueId}/reactions`, { reaction_type: reactionType })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Toggle a reaction on an issue comment */
export async function toggleIssueCommentReaction(templateId, issueId, commentId, reactionType) {
  try {
    const result = await post(`/templates/${templateId}/issues/${issueId}/comments/${commentId}/reactions`, { reaction_type: reactionType })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}
