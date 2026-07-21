/**
 * Variables API
 * Variable and Credential management
 */

import { get, post, patch, del } from './client'
import { ENDPOINTS } from './config'

// ========== Variables ==========

/**
 * List variables with filters
 *
 * S-Grade: Use group_by parameter to get pre-computed groupings from backend.
 *
 * @param {Object} params - Query parameters
 * @param {string} params.scope - 'organization' | 'project' | 'workflow'
 * @param {string} params.scope_id - Scope ID
 * @param {string} params.environment - 'development' | 'staging' | 'production' | 'all'
 * @param {string} params.group_by - 'scope' | 'environment' | 'all' for pre-grouped results
 * @returns {Promise<{ok: boolean, variables: Array, by_scope?: Object, by_environment?: Object}>}
 */
export async function listVariables(params = {}) {
  const queryParams = new URLSearchParams()
  if (params.scope) queryParams.append('scope', params.scope)
  if (params.scope_id) queryParams.append('scope_id', params.scope_id)
  if (params.environment) queryParams.append('environment', params.environment)
  if (params.group_by) queryParams.append('group_by', params.group_by)
  const query = queryParams.toString() ? `?${queryParams.toString()}` : ''
  return get(`${ENDPOINTS.VARIABLES.LIST}${query}`)
}

/**
 * Get single variable
 * @param {string} id - Variable ID
 * @returns {Promise<{ok: boolean, variable: Object}>}
 */
export async function getVariable(id) {
  return get(ENDPOINTS.VARIABLES.GET(id))
}

/**
 * Create variable
 * @param {Object} data - Variable data
 * @param {string} data.name - Variable name
 * @param {string} data.type - 'string' | 'number' | 'boolean' | 'json' | 'secret'
 * @param {any} data.value - Variable value
 * @param {string} data.scope - 'organization' | 'project' | 'workflow'
 * @param {string} data.scope_id - Scope ID
 * @param {string} data.environment - 'development' | 'staging' | 'production' | 'all'
 * @returns {Promise<{ok: boolean, variable: Object}>}
 */
export async function createVariable(data) {
  return post(ENDPOINTS.VARIABLES.CREATE, data)
}

/**
 * Update variable
 * @param {string} id - Variable ID
 * @param {Object} data - Updated fields
 * @returns {Promise<{ok: boolean, variable: Object}>}
 */
export async function updateVariable(id, data) {
  return patch(ENDPOINTS.VARIABLES.UPDATE(id), data)
}

/**
 * Delete variable
 * @param {string} id - Variable ID
 * @returns {Promise<{ok: boolean}>}
 */
export async function deleteVariable(id) {
  return del(ENDPOINTS.VARIABLES.DELETE(id))
}

/**
 * Resolve variables for a workflow (with inheritance)
 * @param {string} workflowId - Workflow ID
 * @param {string} environment - Environment to resolve for
 * @returns {Promise<{ok: boolean, resolved: Object}>}
 */
export async function resolveVariables(workflowId, environment = 'production') {
  return get(`${ENDPOINTS.VARIABLES.RESOLVE(workflowId)}?environment=${environment}`)
}

// ========== Credentials ==========

/**
 * List credentials (metadata only, no values)
 *
 * S-Grade: Use group_by parameter to get pre-computed groupings from backend.
 *
 * @param {Object} params - Query parameters
 * @param {string} params.scope - Credential scope
 * @param {string} params.scope_id - Scope ID
 * @param {string} params.group_by - 'type' | 'scope' | 'all' for pre-grouped results
 * @returns {Promise<{ok: boolean, credentials: Array, by_type?: Object, by_scope?: Object}>}
 */
export async function listCredentials(params = {}) {
  const queryParams = new URLSearchParams()
  if (params.scope) queryParams.append('scope', params.scope)
  if (params.scope_id) queryParams.append('scope_id', params.scope_id)
  if (params.group_by) queryParams.append('group_by', params.group_by)
  const query = queryParams.toString() ? `?${queryParams.toString()}` : ''
  return get(`${ENDPOINTS.VARIABLES.CREDENTIALS}${query}`)
}

/**
 * Create credential
 * @param {Object} data - Credential data
 * @param {string} data.name - Credential name
 * @param {string} data.value - Credential value (will be encrypted)
 * @param {string} data.scope - Scope
 * @param {string} data.scope_id - Scope ID
 * @returns {Promise<{ok: boolean, credential: Object}>}
 */
export async function createCredential(data) {
  return post(ENDPOINTS.VARIABLES.CREDENTIALS, data)
}

/**
 * Reveal credential value (requires reason)
 * @param {string} id - Credential ID
 * @param {string} reason - Reason for access
 * @returns {Promise<{ok: boolean, value: string}>}
 */
export async function revealCredential(id, reason) {
  return post(ENDPOINTS.VARIABLES.CREDENTIAL_REVEAL(id), { reason })
}

/**
 * Delete credential
 * @param {string} id - Credential ID
 * @returns {Promise<{ok: boolean}>}
 */
export async function deleteCredential(id) {
  return del(ENDPOINTS.VARIABLES.CREDENTIAL(id))
}

/**
 * Get credential access audit log
 * @param {Object} params - Query parameters
 * @returns {Promise<{ok: boolean, logs: Array}>}
 */
export async function getCredentialAuditLog(params = {}) {
  const queryParams = new URLSearchParams()
  if (params.credential_id) queryParams.append('credential_id', params.credential_id)
  if (params.limit) queryParams.append('limit', params.limit)
  const query = queryParams.toString() ? `?${queryParams.toString()}` : ''
  return get(`${ENDPOINTS.VARIABLES.CREDENTIAL_AUDIT}${query}`)
}

export default {
  listVariables,
  getVariable,
  createVariable,
  updateVariable,
  deleteVariable,
  resolveVariables,
  listCredentials,
  createCredential,
  revealCredential,
  deleteCredential,
  getCredentialAuditLog
}
