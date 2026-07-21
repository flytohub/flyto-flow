/**
 * Messaging Integrations API
 *
 * API client for managing messaging platform integrations
 * (LINE, Telegram, Slack, Discord, etc.)
 */

import apiClient from './client'

// =============================================================================
// Providers
// =============================================================================

/**
 * Get available messaging providers
 * @returns {Promise<{ok: boolean, providers: Array}>}
 */
export async function getProviders() {
  const response = await apiClient.get('/messaging/providers')
  return response.data
}

/**
 * Get configuration schema for a provider
 * @param {string} provider - Provider name (line, telegram, etc.)
 * @returns {Promise<{ok: boolean, configSchema: Object}>}
 */
export async function getProviderSchema(provider) {
  const response = await apiClient.get(`/messaging/providers/${provider}`)
  return response.data
}

// =============================================================================
// Integrations CRUD
// =============================================================================

/**
 * List user's messaging integrations
 * @param {Object} params - Query parameters
 * @param {string} [params.provider] - Filter by provider
 * @param {string} [params.status] - Filter by status (active, disabled)
 * @param {number} [params.limit=50] - Max results
 * @param {number} [params.offset=0] - Pagination offset
 * @returns {Promise<{ok: boolean, integrations: Array, total: number}>}
 */
export async function listIntegrations(params = {}) {
  const response = await apiClient.get('/messaging/integrations', { params })
  return response.data
}

/**
 * Get integration details
 * @param {string} integrationId - Integration ID
 * @returns {Promise<{ok: boolean, integration: Object, webhookUrl: string}>}
 */
export async function getIntegration(integrationId) {
  const response = await apiClient.get(`/messaging/integrations/${integrationId}`)
  return response.data
}

/**
 * Create a new integration
 * @param {Object} data - Integration data
 * @param {string} data.provider - Provider name
 * @param {string} data.name - Integration name
 * @param {Object} data.config - Provider-specific configuration
 * @param {string} [data.description] - Description
 * @param {string} [data.defaultWorkflowId] - Default workflow to execute
 * @returns {Promise<{ok: boolean, integration: Object, webhookUrl: string}>}
 */
export async function createIntegration(data) {
  const response = await apiClient.post('/messaging/integrations', data)
  return response.data
}

/**
 * Update an integration
 * @param {string} integrationId - Integration ID
 * @param {Object} data - Fields to update
 * @returns {Promise<{ok: boolean, integration: Object}>}
 */
export async function updateIntegration(integrationId, data) {
  const response = await apiClient.patch(`/messaging/integrations/${integrationId}`, data)
  return response.data
}

/**
 * Delete an integration
 * @param {string} integrationId - Integration ID
 * @returns {Promise<{ok: boolean}>}
 */
export async function deleteIntegration(integrationId) {
  const response = await apiClient.delete(`/messaging/integrations/${integrationId}`)
  return response.data
}

// =============================================================================
// Integration Actions
// =============================================================================

/**
 * Test integration connection
 * @param {string} integrationId - Integration ID
 * @returns {Promise<{ok: boolean, botName?: string, botId?: string, error?: string}>}
 */
export async function testIntegration(integrationId) {
  const response = await apiClient.post(`/messaging/integrations/${integrationId}/test`)
  return response.data
}

/**
 * Enable an integration
 * @param {string} integrationId - Integration ID
 * @returns {Promise<{ok: boolean, integration: Object}>}
 */
export async function enableIntegration(integrationId) {
  const response = await apiClient.post(`/messaging/integrations/${integrationId}/enable`)
  return response.data
}

/**
 * Disable an integration
 * @param {string} integrationId - Integration ID
 * @returns {Promise<{ok: boolean, integration: Object}>}
 */
export async function disableIntegration(integrationId) {
  const response = await apiClient.post(`/messaging/integrations/${integrationId}/disable`)
  return response.data
}

// =============================================================================
// Export all functions
// =============================================================================

export default {
  // Providers
  getProviders,
  getProviderSchema,

  // Integrations CRUD
  listIntegrations,
  getIntegration,
  createIntegration,
  updateIntegration,
  deleteIntegration,

  // Actions
  testIntegration,
  enableIntegration,
  disableIntegration,
}
