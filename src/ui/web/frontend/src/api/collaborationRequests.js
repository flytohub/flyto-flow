/**
 * Collaboration Requests API
 *
 * Handles requesting, checking, listing, and resolving
 * collaboration access for locked templates.
 */

import { getApiUrl } from '@/config/api'
import { authAPI } from '@/api/auth'

async function authFetch(path, options = {}) {
  const token = await authAPI.getIdToken()
  const url = `${getApiUrl()}${path}`
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${res.status})`)
  }
  return res.json()
}

/**
 * Request collaboration access to a template
 */
export async function requestCollaboration(templateId, message = '') {
  return authFetch(`/api/collaboration/request/${templateId}`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

/**
 * Check current user's request status for a template
 */
export async function getMyRequestStatus(templateId) {
  return authFetch(`/api/collaboration/request/${templateId}/status`)
}

/**
 * List collaboration requests for a template (owner only)
 */
export async function listCollaborationRequests(templateId, status = 'pending') {
  const query = status ? `?status=${status}` : ''
  return authFetch(`/api/collaboration/requests/${templateId}${query}`)
}

/**
 * Approve or reject a collaboration request (owner only)
 */
export async function resolveCollaborationRequest(requestId, action) {
  return authFetch(`/api/collaboration/requests/${requestId}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ action }),
  })
}
