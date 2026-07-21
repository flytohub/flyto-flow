/**
 * Templates API - Pull Request Operations
 */

import { get, post, put, del } from '@/api/client'

/** List pull requests for a template with optional status filter and pagination */
export async function listPullRequests(templateId, { status, page = 1, pageSize = 20 } = {}) {
  try {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    params.append('page', page)
    params.append('page_size', pageSize)

    const result = await get(`/templates/${templateId}/pull-requests?${params}`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Get a single pull request by ID */
export async function getPullRequest(templateId, prId) {
  try {
    const result = await get(`/templates/${templateId}/pull-requests/${prId}`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Create a new pull request from a fork */
export async function createPullRequest(templateId, { forkId, title, description, isDraft = false, linkedIssueIds = [] }) {
  try {
    const result = await post(`/templates/${templateId}/pull-requests`, {
      fork_id: forkId,
      title,
      description,
      is_draft: isDraft,
      linked_issue_ids: linkedIssueIds,
    })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Submit a review (approve/request changes) on a pull request */
export async function reviewPullRequest(templateId, prId, { action, comment }) {
  try {
    const result = await post(`/templates/${templateId}/pull-requests/${prId}/review`, {
      action,
      comment,
    })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Merge an approved pull request */
export async function mergePullRequest(templateId, prId) {
  try {
    const result = await post(`/templates/${templateId}/pull-requests/${prId}/merge`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Close a pull request without merging */
export async function closePullRequest(templateId, prId) {
  try {
    const result = await post(`/templates/${templateId}/pull-requests/${prId}/close`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Reopen a previously closed pull request */
export async function reopenPullRequest(templateId, prId) {
  try {
    const result = await post(`/templates/${templateId}/pull-requests/${prId}/reopen`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Mark a draft pull request as ready for review */
export async function markPRReady(templateId, prId) {
  try {
    const result = await post(`/templates/${templateId}/pull-requests/${prId}/ready`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Update labels on a pull request */
export async function updatePRLabels(templateId, prId, labels) {
  try {
    const result = await put(`/templates/${templateId}/pull-requests/${prId}/labels`, { labels })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** List comments on a pull request with pagination */
export async function listPRComments(templateId, prId, { page = 1, pageSize = 50 } = {}) {
  try {
    const params = new URLSearchParams()
    params.append('page', page)
    params.append('page_size', pageSize)

    const result = await get(`/templates/${templateId}/pull-requests/${prId}/comments?${params}`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Add a comment to a pull request */
export async function createPRComment(templateId, prId, { content }) {
  try {
    const result = await post(`/templates/${templateId}/pull-requests/${prId}/comments`, { content })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Update an existing pull request comment */
export async function updatePRComment(templateId, prId, commentId, { content }) {
  try {
    const result = await put(`/templates/${templateId}/pull-requests/${prId}/comments/${commentId}`, { content })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Delete a comment from a pull request */
export async function deletePRComment(templateId, prId, commentId) {
  try {
    const result = await del(`/templates/${templateId}/pull-requests/${prId}/comments/${commentId}`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Toggle a reaction on a pull request */
export async function togglePRReaction(templateId, prId, reactionType) {
  try {
    const result = await post(`/templates/${templateId}/pull-requests/${prId}/reactions`, { reaction_type: reactionType })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Toggle a reaction on a pull request comment */
export async function togglePRCommentReaction(templateId, prId, commentId, reactionType) {
  try {
    const result = await post(`/templates/${templateId}/pull-requests/${prId}/comments/${commentId}/reactions`, { reaction_type: reactionType })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Check if a pull request is eligible to be merged */
export async function mergeCheck(templateId, prId) {
  try {
    const result = await get(`/templates/${templateId}/pull-requests/${prId}/merge-check`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/** Link an issue to a pull request */
export async function linkIssueToPR(templateId, prId, issueId) {
  try {
    const result = await post(`/templates/${templateId}/pull-requests/${prId}/link-issue`, { issue_id: issueId })
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}
