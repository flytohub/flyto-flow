/**
 * WebSocket Connection Manager
 *
 * S-Grade: WebSocket connection for module sync.
 * Single responsibility: Manage WebSocket lifecycle.
 */

import { getWsUrl } from '@/config/api'
import { DEFAULTS } from '@/config/defaults'
import { clearModuleCache, setCachedVersion } from './cacheUtils'

/**
 * Create WebSocket connection manager
 * @param {Object} options
 * @param {Ref} options.isConnected - Connection state ref
 * @param {Ref} options.currentVersion - Version ref
 * @param {Ref} options.lastUpdate - Last update ref
 * @param {Ref} options.error - Error ref
 * @param {Function} options.startPolling - Fallback polling function
 * @returns {Object} Connection manager
 */
export function createWebSocketManager(options) {
  const { isConnected, currentVersion, lastUpdate, error, startPolling } = options

  let ws = null
  let reconnectTimeout = null

  /**
   * Handle WebSocket message
   */
  function handleMessage(event) {
    try {
      const data = JSON.parse(event.data)

      switch (data.type) {
        case 'modules_updated':
          lastUpdate.value = data.updatedAt
          currentVersion.value = data.version

          // Clear cache
          clearModuleCache()
          setCachedVersion(data.version)

          // Emit event
          window.dispatchEvent(new CustomEvent('modules-updated', {
            detail: data
          }))
          break

        case 'heartbeat':
          // Keep-alive, no action needed
          break

        case 'version':
          currentVersion.value = data.version
          lastUpdate.value = data.updatedAt
          break

        case 'pong':
          // Response to ping
          break

        case 'frontend_updated':
          window.dispatchEvent(new CustomEvent('frontend-updated', { detail: data }))
          if (data.action === 'reload') {
            setTimeout(() => window.location.reload(), 3000)
          }
          break

        default:
          break
      }
    } catch (e) {
      // Silent fail
    }
  }

  /**
   * Connect to WebSocket
   */
  function connect(pollInterval) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      return
    }

    // Resolve at connect time so the current local origin is used.
    const wsUrl = `${getWsUrl()}/ws/modules`

    try {
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        isConnected.value = true
        error.value = null

        // Stop polling when WebSocket is connected
        if (pollInterval.value) {
          clearInterval(pollInterval.value)
          pollInterval.value = null
        }

        // Request current version
        ws.send(JSON.stringify({ type: 'get_version' }))
      }

      ws.onmessage = handleMessage

      ws.onclose = () => {
        isConnected.value = false

        // Start polling as fallback
        startPolling()

        // Clear any existing reconnect timeout
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout)
          reconnectTimeout = null
        }

        // Attempt to reconnect after delay
        reconnectTimeout = setTimeout(() => {
          reconnectTimeout = null
          connect(pollInterval)
        }, DEFAULTS.TIMING.MODULE_SYNC_RECONNECT)
      }

      ws.onerror = () => {
        error.value = 'WebSocket connection failed'
        isConnected.value = false
      }
    } catch (e) {
      error.value = e.message
      startPolling()
    }
  }

  /**
   * Disconnect WebSocket
   */
  function disconnect(pollInterval) {
    if (ws) {
      ws.close()
      ws = null
    }
    if (pollInterval.value) {
      clearInterval(pollInterval.value)
      pollInterval.value = null
    }
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
    isConnected.value = false
  }

  return {
    connect,
    disconnect
  }
}
