/**
 * Module Sync Core Composable
 *
 * S-Grade: Main module sync composable.
 * Single responsibility: Compose sync functionality.
 */

import { ref, onMounted, onUnmounted, computed } from 'vue'
import { DEFAULTS } from '@/config/defaults'
import { clearModuleCache, getCachedVersion } from './cacheUtils'
import { checkForModuleUpdates, triggerModuleReload } from './versionCheck'
import { createWebSocketManager } from './websocket'

export function useModuleSync() {
  const isConnected = ref(false)
  const lastUpdate = ref(null)
  const currentVersion = ref(null)
  const isReloading = ref(false)
  const error = ref(null)

  const pollInterval = ref(null)

  /**
   * Start polling as fallback
   */
  function startPolling() {
    if (pollInterval.value) return

    pollInterval.value = setInterval(() => {
      checkForModuleUpdates((versionInfo) => {
        currentVersion.value = versionInfo.version
        lastUpdate.value = versionInfo.updatedAt
      })
    }, DEFAULTS.TIMING.MODULE_SYNC_POLL)
  }

  // Create WebSocket manager
  const wsManager = createWebSocketManager({
    isConnected,
    currentVersion,
    lastUpdate,
    error,
    startPolling
  })

  /**
   * Check for updates wrapper
   */
  async function checkForUpdates() {
    return checkForModuleUpdates((versionInfo) => {
      currentVersion.value = versionInfo.version
      lastUpdate.value = versionInfo.updatedAt
    })
  }

  /**
   * Trigger reload wrapper
   */
  async function triggerReload(options = {}) {
    isReloading.value = true
    error.value = null

    try {
      const result = await triggerModuleReload(options)
      return result
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      isReloading.value = false
    }
  }

  /**
   * Connect wrapper
   */
  function connect() {
    wsManager.connect(pollInterval)
  }

  /**
   * Disconnect wrapper
   */
  function disconnect() {
    wsManager.disconnect(pollInterval)
  }

  // Lifecycle
  onMounted(() => {
    // Get cached version
    currentVersion.value = getCachedVersion()

    // Try WebSocket first, fallback to polling
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    // State
    isConnected,
    lastUpdate,
    currentVersion,
    isReloading,
    error,

    // Computed
    connectionStatus: computed(() => {
      if (isConnected.value) return 'connected'
      if (pollInterval.value) return 'polling'
      return 'disconnected'
    }),

    // Actions
    connect,
    disconnect,
    checkForUpdates,
    triggerReload,
    clearCache: clearModuleCache,
  }
}

/**
 * Listen for module updates (for use outside Vue components)
 */
export function onModulesUpdated(callback) {
  const handler = (event) => callback(event.detail)
  window.addEventListener('modules-updated', handler)
  return () => window.removeEventListener('modules-updated', handler)
}
