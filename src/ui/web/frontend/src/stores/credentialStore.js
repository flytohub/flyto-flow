/**
 * Credential Store - Secure Credential Management
 * Manages API keys, secrets, and credential audit logging
 *
 * Split from variableStore.js for single responsibility:
 * - variableStore: Environment variables
 * - credentialStore: Secure credentials with audit logging
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import variablesAPI from '@/api/variables'
import { telemetry } from '@/services/telemetry'

export const useCredentialStore = defineStore('credentials', () => {
  // ========== State ==========
  const credentials = ref([])
  const auditLog = ref([])
  const typeSchemas = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  // ========== S-Grade: Backend-computed groups ==========
  const credentialsByType = ref({
    apiKey: [],
    oauth: [],
    password: [],
    token: [],
    other: []
  })

  // ========== Getters ==========
  const hasCredentials = computed(() => credentials.value.length > 0)

  // ========== Actions ==========

  /**
   * Fetch credentials list
   *
   * S-Grade: Requests pre-grouped data from backend.
   *
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Result
   */
  async function fetchCredentials(params = {}) {
    isLoading.value = true
    error.value = null

    try {
      // S-Grade: Request type grouping from backend
      const result = await variablesAPI.listCredentials({
        ...params,
        groupBy: 'type'
      })

      if (result.ok) {
        credentials.value = result.credentials || []

        // Store type schemas from backend
        if (result.type_schemas) {
          typeSchemas.value = result.type_schemas
        }

        // S-Grade: Use backend-computed groups
        if (result.byType) {
          credentialsByType.value = result.byType
        }
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to fetch credentials'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create credential
   * @param {Object} data - Credential data
   * @returns {Promise<Object>} Result
   */
  async function createCredential(data) {
    isLoading.value = true
    error.value = null

    try {
      const result = await variablesAPI.createCredential(data)

      if (result.ok) {
        credentials.value.push(result.credential)

        // Track credential creation
        telemetry.track('credential.create', {
          type: data.type
        })
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to create credential'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Reveal credential value
   * @param {string} id - Credential ID
   * @param {string} reason - Access reason
   * @returns {Promise<Object>} Result with value
   */
  async function revealCredential(id, reason) {
    isLoading.value = true
    error.value = null

    try {
      const result = await variablesAPI.revealCredential(id, reason)

      if (!result.ok) {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to reveal credential'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update credential
   * @param {string} id - Credential ID
   * @param {Object} data - Updated data
   * @returns {Promise<Object>} Result
   */
  async function updateCredential(id, data) {
    isLoading.value = true
    error.value = null

    try {
      const result = await variablesAPI.updateCredential(id, data)

      if (result.ok) {
        const index = credentials.value.findIndex(c => c.id === id)
        if (index !== -1) {
          credentials.value[index] = result.credential
        }
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to update credential'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete credential
   * @param {string} id - Credential ID
   * @returns {Promise<Object>} Result
   */
  async function deleteCredential(id) {
    isLoading.value = true
    error.value = null

    try {
      const result = await variablesAPI.deleteCredential(id)

      if (result.ok) {
        credentials.value = credentials.value.filter(c => c.id !== id)

        // Track credential deletion
        telemetry.track('credential.delete', {
          credential_id: id
        })
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to delete credential'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch credential audit log
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Result
   */
  async function fetchAuditLog(params = {}) {
    isLoading.value = true
    error.value = null

    try {
      const result = await variablesAPI.getCredentialAuditLog(params)

      if (result.ok) {
        auditLog.value = result.logs || []
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to fetch audit log'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

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
    credentials.value = []
    auditLog.value = []
    // S-Grade: Reset backend-computed groups
    credentialsByType.value = { apiKey: [], oauth: [], password: [], token: [], other: [] }
    isLoading.value = false
    error.value = null
  }

  return {
    // State
    credentials,
    auditLog,
    typeSchemas,
    isLoading,
    error,

    // Getters
    hasCredentials,
    credentialsByType,

    // Actions
    fetchCredentials,
    createCredential,
    revealCredential,
    updateCredential,
    deleteCredential,
    fetchAuditLog,
    clearError,
    reset
  }
})
