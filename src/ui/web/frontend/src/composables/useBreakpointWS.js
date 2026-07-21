/**
 * Breakpoint WebSocket Composable
 *
 * Global listener for real-time breakpoint notifications.
 * When an interact breakpoint arrives, emits an event so
 * the global dialog can pop up regardless of current page.
 */

import { ref, onMounted, onUnmounted } from 'vue'

const pendingInteract = ref(null)
const isConnected = ref(false)

// Singleton WebSocket state — intentionally module-level.
// Only one breakpoint WS connection should exist per app (mounted at App.vue).
// These are NOT per-component state; multiple useBreakpointWS() calls share
// the same connection and reactive refs.
let ws = null
let reconnectTimeout = null
let reconnectAttempts = 0
const MAX_RECONNECT_DELAY = 30000

function getWsUrl() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  // Append sidecar secret if available
  const secret = document.cookie
    .split('; ')
    .find(c => c.startsWith('_flyto_secret='))
    ?.split('=')[1]
  const params = secret ? `?_secret=${secret}` : ''
  return `${proto}//${host}/ws/breakpoints${params}`
}

function connect() {
  if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
    return
  }

  try {
    ws = new WebSocket(getWsUrl())
  } catch (e) {
    scheduleReconnect()
    return
  }

  ws.onopen = () => {
    isConnected.value = true
    reconnectAttempts = 0
  }

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      handleMessage(msg)
    } catch (e) {
      // ignore non-JSON
    }
  }

  ws.onclose = () => {
    isConnected.value = false
    scheduleReconnect()
  }

  ws.onerror = () => {
    isConnected.value = false
  }
}

function scheduleReconnect() {
  if (reconnectTimeout) return
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY)
  reconnectAttempts++
  reconnectTimeout = setTimeout(() => {
    reconnectTimeout = null
    connect()
  }, delay)
}

function handleMessage(msg) {
  if (msg.type === 'breakpoint.pending') {
    const bp = msg.breakpoint
    const ctx = bp?.context_snapshot || bp?.contextSnapshot || {}
    if (ctx._interact === true) {
      // New interact breakpoint — notify global listener
      pendingInteract.value = bp
      window.dispatchEvent(new CustomEvent('flyto-interact-breakpoint', {
        detail: bp
      }))
    }
  } else if (msg.type === 'breakpoint.resolved') {
    // If the resolved breakpoint is the one we're showing, clear it
    if (pendingInteract.value) {
      const currentId = pendingInteract.value.breakpoint_id || pendingInteract.value.breakpointId
      if (currentId === msg.breakpoint_id) {
        pendingInteract.value = null
      }
    }
  }
}

function disconnect() {
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout)
    reconnectTimeout = null
  }
  if (ws) {
    ws.onclose = null // prevent reconnect
    ws.close()
    ws = null
  }
  isConnected.value = false
}

/**
 * useBreakpointWS - call once at App.vue level to enable global breakpoint listening
 */
export function useBreakpointWS() {
  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    pendingInteract,
    isConnected,
    clearInteract: () => { pendingInteract.value = null },
  }
}

/**
 * useGlobalInteract - used by the global interact dialog component
 * to reactively get/clear the pending interact breakpoint
 */
export function useGlobalInteract() {
  return {
    pendingInteract,
    clearInteract: () => { pendingInteract.value = null },
  }
}
