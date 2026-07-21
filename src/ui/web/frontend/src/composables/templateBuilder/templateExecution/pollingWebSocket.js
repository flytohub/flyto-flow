/**
 * Polling WebSocket Functions
 *
 * WebSocket connection management for execution browser events.
 * Extracted from createPollingActions for reduced complexity.
 */

import { getWsUrl } from '@/config/api'

/**
 * Connect to execution WebSocket for instant browser + step events.
 * Listens for browser_available / browser_closed + step_completed for real-time Preview Results.
 * @param {Object} config - Connection config
 * @param {string} config.executionId - Current execution ID
 * @param {Object} config.hasBrowser - Reactive ref for hasBrowser state
 * @param {Object|null} config.wsRef - Object holding current WebSocket reference { ws }
 * @param {Function} config.disconnectFn - Function to disconnect existing WebSocket
 * @param {Function} [config.onStepCompleted] - Callback for step_completed events
 * @param {Function} [config.onAgentEvent] - Callback for agent streaming events (tool_call, iteration, tool_result)
 */
export function connectExecWs(config) {
  const { executionId, hasBrowser, wsRef, disconnectFn, onStepCompleted, onAgentEvent } = config
  disconnectFn()
  if (!executionId) return
  try {
    const url = `${getWsUrl()}/ws/executions/${executionId}`
    wsRef.ws = new WebSocket(url)
    wsRef.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'browser_available') {
          hasBrowser.value = true
        } else if (msg.type === 'browser_closed') {
          hasBrowser.value = false
        } else if (msg.type === 'step_completed' && onStepCompleted) {
          onStepCompleted(msg)
        } else if (msg.type?.startsWith('agent:') && onAgentEvent) {
          onAgentEvent(msg)
        } else if (msg.type === 'plugin_ui_open' || msg.type === 'plugin_ui_close') {
          // Dispatch to PluginUIOverlay via CustomEvent
          window.dispatchEvent(new CustomEvent('flyto-plugin-ui', { detail: msg }))
        }
      } catch (err) { console.warn('[pollingWebSocket]', err) }
    }
    wsRef.ws.onerror = () => {} // silent — polling is the fallback
  } catch (err) { console.warn('[pollingWebSocket]', err) }
}

/**
 * Disconnect execution WebSocket and clean up handlers.
 * @param {Object} wsRef - Object holding current WebSocket reference { ws }
 */
export function disconnectExecWs(wsRef) {
  if (wsRef.ws) {
    wsRef.ws.onmessage = null
    wsRef.ws.onclose = null
    wsRef.ws.onerror = null
    wsRef.ws.close()
    wsRef.ws = null
  }
}
