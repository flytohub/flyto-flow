/**
 * Messaging Integrations Store
 *
 * Pinia store for managing messaging platform integrations state.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import messagingApi from '@/api/messaging'

export const useMessagingStore = defineStore('messaging', () => {
  // ==========================================================================
  // State
  // ==========================================================================

  const providers = ref([])
  const integrations = ref([])
  const currentIntegration = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // ==========================================================================
  // Getters
  // ==========================================================================

  const getProvider = computed(() => (name) =>
    providers.value.find(p => p.name === name)
  )

  // ==========================================================================
  // Actions
  // ==========================================================================

  /**
   * Load available providers
   */
  async function loadProviders() {
    try {
      const result = await messagingApi.getProviders()
      if (result.ok) {
        providers.value = result.providers
      }
    } catch (e) {
      console.error('Failed to load providers:', e)
    }
  }

  /**
   * Load user's integrations
   */
  async function loadIntegrations(params = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await messagingApi.listIntegrations(params)
      if (result.ok) {
        integrations.value = result.integrations
      } else {
        error.value = result.error || 'Failed to load integrations'
      }
    } catch (e) {
      error.value = e.message
      console.error('Failed to load integrations:', e)
    } finally {
      loading.value = false
    }
  }

  /**
   * Get integration by ID
   */
  async function loadIntegration(integrationId) {
    loading.value = true
    error.value = null

    try {
      const result = await messagingApi.getIntegration(integrationId)
      if (result.ok) {
        currentIntegration.value = result.integration
        currentIntegration.value.webhookUrl = result.webhookUrl
        return result.integration
      } else {
        error.value = result.error || 'Integration not found'
        return null
      }
    } catch (e) {
      error.value = e.message
      console.error('Failed to load integration:', e)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new integration
   */
  async function createIntegration(data) {
    loading.value = true
    error.value = null

    try {
      const result = await messagingApi.createIntegration(data)
      if (result.ok) {
        integrations.value.push(result.integration)
        return result
      } else {
        error.value = result.error || 'Failed to create integration'
        return result
      }
    } catch (e) {
      error.value = e.message
      console.error('Failed to create integration:', e)
      return { ok: false, error: e.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * Update an integration
   */
  async function updateIntegration(integrationId, data) {
    loading.value = true
    error.value = null

    try {
      const result = await messagingApi.updateIntegration(integrationId, data)
      if (result.ok) {
        // Update in list
        const index = integrations.value.findIndex(i => i.id === integrationId)
        if (index >= 0) {
          integrations.value[index] = result.integration
        }
        // Update current if same
        if (currentIntegration.value?.id === integrationId) {
          currentIntegration.value = result.integration
        }
        return result
      } else {
        error.value = result.error || 'Failed to update integration'
        return result
      }
    } catch (e) {
      error.value = e.message
      console.error('Failed to update integration:', e)
      return { ok: false, error: e.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete an integration
   */
  async function deleteIntegration(integrationId) {
    loading.value = true
    error.value = null

    try {
      const result = await messagingApi.deleteIntegration(integrationId)
      if (result.ok) {
        integrations.value = integrations.value.filter(i => i.id !== integrationId)
        if (currentIntegration.value?.id === integrationId) {
          currentIntegration.value = null
        }
        return result
      } else {
        error.value = result.error || 'Failed to delete integration'
        return result
      }
    } catch (e) {
      error.value = e.message
      console.error('Failed to delete integration:', e)
      return { ok: false, error: e.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * Test integration connection
   */
  async function testIntegration(integrationId) {
    try {
      return await messagingApi.testIntegration(integrationId)
    } catch (e) {
      console.error('Failed to test integration:', e)
      return { ok: false, error: e.message }
    }
  }

  /**
   * Enable/disable integration
   */
  async function toggleIntegration(integrationId, enable) {
    try {
      const result = enable
        ? await messagingApi.enableIntegration(integrationId)
        : await messagingApi.disableIntegration(integrationId)

      if (result.ok) {
        const index = integrations.value.findIndex(i => i.id === integrationId)
        if (index >= 0) {
          integrations.value[index] = result.integration
        }
      }

      return result
    } catch (e) {
      console.error('Failed to toggle integration:', e)
      return { ok: false, error: e.message }
    }
  }

  /**
   * Clear current integration
   */
  function clearCurrent() {
    currentIntegration.value = null
  }

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // State
    providers,
    integrations,
    currentIntegration,
    loading,
    error,

    // Getters
    getProvider,

    // Actions
    loadProviders,
    loadIntegrations,
    loadIntegration,
    createIntegration,
    updateIntegration,
    deleteIntegration,
    testIntegration,
    toggleIntegration,
    clearCurrent,
  }
})
