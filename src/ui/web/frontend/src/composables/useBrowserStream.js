/**
 * Browser Screencast WebSocket Composable
 *
 * Connects to /ws/browser/{executionId} for real-time browser viewing.
 * Handles binary JPEG frames → canvas rendering, and input capture → JSON messages.
 */

import { ref, onUnmounted, watch } from 'vue'
import { getWsUrl } from '@/config/api'
import { DEFAULTS } from '@/config/defaults'
import { authAPI } from '@/api/auth'

export function useBrowserStream(executionId, { wsUrlOverride, cloudMode } = {}) {
  const isConnected = ref(false)
  const isStreaming = ref(false)
  const viewerCount = ref(0)
  const hasControl = ref(false)
  const driverUserId = ref(null)
  const viewers = ref([])
  const controlRequest = ref(null) // { user_id, user_name }
  const viewport = ref({ width: 1280, height: 720 })
  const canvasRef = ref(null)
  const serverStopped = ref(false) // true only when server sends screencast.stopped
  const idleTimeout = ref(0) // total idle timeout in seconds (0 = not idle)
  const idleRemaining = ref(0) // seconds remaining before browser closes
  let _idleInterval = null

  let ws = null
  let reconnectTimeout = null
  let reconnectAttempts = 0
  const MAX_RECONNECT = DEFAULTS.WEBSOCKET.MAX_RECONNECT_ATTEMPTS

  // Current user info (passed from parent)
  let _userId = ''
  let _userName = 'Anonymous'

  function connect(userId = '', userName = 'Anonymous') {
    _userId = userId
    _userName = userName
    serverStopped.value = false
    _connect()
  }

  function _connect() {
    if (ws) {
      disconnect()
    }

    const eid = typeof executionId === 'object' && executionId.value !== undefined
      ? executionId.value
      : executionId
    if (!eid) return

    const wsBase = getWsUrl()
    // Validated token — avoids opening a WebSocket that will instantly 1008
    // on an expired Bearer and puts us into reconnect-storm territory.
    const token = authAPI.getAccessToken()
    let url
    if (cloudMode || wsUrlOverride) {
      // Cloud mode: connect to relay endpoint (view-only, binary frames only)
      const relayPath = wsUrlOverride || `/ws/browser-relay/${eid}`
      url = `${wsBase}${relayPath}${token ? '?token=' + token : ''}`
    } else {
      // Desktop mode: connect to Worker's /ws/browser/{executionId}
      const params = new URLSearchParams()
      if (_userId) params.set('user_id', _userId)
      if (_userName) params.set('user_name', _userName)
      if (token) params.set('token', token)
      const paramStr = params.toString()
      url = `${wsBase}/ws/browser/${eid}${paramStr ? '?' + paramStr : ''}`
    }

    ws = new WebSocket(url)
    ws.binaryType = 'arraybuffer'

    ws.onopen = () => {
      isConnected.value = true
      reconnectAttempts = 0
    }

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        // Binary JPEG frame — mark streaming on first frame
        // (relay mode has no screencast.started JSON message)
        if (!isStreaming.value) isStreaming.value = true
        _renderFrame(event.data)
      } else {
        // JSON control message
        try {
          const msg = JSON.parse(event.data)
          _handleMessage(msg)
        } catch {
          // ignore
        }
      }
    }

    ws.onclose = () => {
      isConnected.value = false
      isStreaming.value = false
      _scheduleReconnect()
    }

    ws.onerror = () => {
      // onclose will fire after this
    }
  }

  function disconnect() {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
    reconnectAttempts = MAX_RECONNECT // prevent reconnect
    if (ws) {
      ws.onclose = null // prevent reconnect trigger
      ws.close()
      ws = null
    }
    isConnected.value = false
    isStreaming.value = false
    // Clean up rendering resources
    if (_rafId) { cancelAnimationFrame(_rafId); _rafId = null }
    if (_latestBitmap) { _latestBitmap.close(); _latestBitmap = null }
    _nextBuffer = null
    _decoding = false
    _ctx = null
    _firstFrame = true
  }

  function _scheduleReconnect() {
    if (reconnectAttempts >= MAX_RECONNECT) return
    reconnectAttempts++
    const delay = DEFAULTS.WEBSOCKET.RECONNECT_INTERVAL * reconnectAttempts
    reconnectTimeout = setTimeout(_connect, delay)
  }

  function _handleMessage(msg) {
    switch (msg.type) {
      case 'welcome':
        // Server assigns user_id (e.g. anon_xxx when none provided)
        if (msg.user_id) {
          _userId = msg.user_id
        }
        break

      case 'screencast.started':
        isStreaming.value = true
        serverStopped.value = false
        if (msg.viewport) {
          viewport.value = msg.viewport
        }
        break

      case 'screencast.stopped':
        isStreaming.value = false
        serverStopped.value = true // server-initiated stop (browser.close)
        _stopIdleCountdown()
        break

      case 'browser_idle':
        // Server signals browser is idle after workflow completion
        _startIdleCountdown(msg.timeout_seconds || 300)
        break

      case 'control.state':
        driverUserId.value = msg.driver_user_id
        viewers.value = msg.viewers || []
        hasControl.value = msg.driver_user_id === _userId
        break

      case 'control.granted':
        driverUserId.value = msg.user_id
        hasControl.value = msg.user_id === _userId
        break

      case 'control.released':
        if (msg.user_id === _userId) {
          hasControl.value = false
        }
        break

      case 'control.requested':
        controlRequest.value = {
          user_id: msg.user_id,
          user_name: msg.user_name || 'Anonymous',
        }
        break

      case 'viewer.count':
        viewerCount.value = msg.count
        break
    }
  }

  // --- Frame Rendering ---
  // Pipeline: WS binary → createImageBitmap (async decode) → requestAnimationFrame → drawImage
  // Always keeps the latest decoded bitmap; rAF ensures we paint at display refresh rate.

  let _latestBitmap = null  // most recently decoded ImageBitmap
  let _rafId = null         // requestAnimationFrame handle
  let _decoding = false     // guard concurrent createImageBitmap calls
  let _nextBuffer = null    // buffer waiting for decode
  let _firstFrame = true    // paint first frame immediately (skip rAF)

  function _renderFrame(buffer) {
    _nextBuffer = buffer
    if (!_decoding) _decodeNext()
  }

  function _decodeNext() {
    if (!_nextBuffer) return
    const buf = _nextBuffer
    _nextBuffer = null
    _decoding = true

    const blob = new Blob([buf], { type: 'image/jpeg' })
    createImageBitmap(blob).then((bitmap) => {
      if (_latestBitmap) _latestBitmap.close()
      _latestBitmap = bitmap
      // First frame: paint immediately for instant display
      if (_firstFrame) {
        _firstFrame = false
        _paint()
      } else {
        _scheduleRaf()
      }
      _decoding = false
      _decodeNext()
    }).catch(() => {
      _decoding = false
      _decodeNext()
    })
  }

  function _scheduleRaf() {
    if (_rafId) return
    _rafId = requestAnimationFrame(_paint)
  }

  let _ctx = null

  function _paint() {
    _rafId = null
    const bitmap = _latestBitmap
    if (!bitmap) return

    const canvas = canvasRef.value
    if (!canvas) return

    if (canvas.width !== viewport.value.width || canvas.height !== viewport.value.height) {
      canvas.width = viewport.value.width
      canvas.height = viewport.value.height
      _ctx = null
    }

    if (!_ctx) {
      _ctx = canvas.getContext('2d', { alpha: false, desynchronized: true })
    }

    _ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
  }

  // --- Input Sending ---

  function _sendJSON(msg) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg))
    }
  }

  function _getScaledCoords(event) {
    const canvas = canvasRef.value
    if (!canvas) return { x: 0, y: 0 }
    const scaleX = viewport.value.width / canvas.clientWidth
    const scaleY = viewport.value.height / canvas.clientHeight
    return {
      x: Math.round(event.offsetX * scaleX),
      y: Math.round(event.offsetY * scaleY),
    }
  }

  function _getModifiers(event) {
    let modifiers = 0
    if (event.altKey) modifiers |= 1
    if (event.ctrlKey) modifiers |= 2
    if (event.metaKey) modifiers |= 4
    if (event.shiftKey) modifiers |= 8
    return modifiers
  }

  function _getButtonName(button) {
    switch (button) {
      case 0: return 'left'
      case 1: return 'middle'
      case 2: return 'right'
      default: return 'left'
    }
  }

  function _resetIdleOnInput() {
    // When user interacts, server resets idle timer and sends new browser_idle event
    // Frontend countdown will restart when new browser_idle arrives
    if (idleRemaining.value > 0) {
      _stopIdleCountdown()
    }
  }

  function sendMouseClick(event) {
    const { x, y } = _getScaledCoords(event)
    _sendJSON({ type: 'mouse.click', x, y, button: _getButtonName(event.button) })
    _resetIdleOnInput()
  }

  function sendMouseDown(event) {
    const { x, y } = _getScaledCoords(event)
    _sendJSON({ type: 'mouse.down', x, y, button: _getButtonName(event.button) })
    _resetIdleOnInput()
  }

  function sendMouseUp(event) {
    const { x, y } = _getScaledCoords(event)
    _sendJSON({ type: 'mouse.up', x, y, button: _getButtonName(event.button) })
  }

  function sendMouseMove(event) {
    const { x, y } = _getScaledCoords(event)
    _sendJSON({ type: 'mouse.move', x, y })
  }

  function sendWheel(event) {
    const { x, y } = _getScaledCoords(event)
    _sendJSON({ type: 'mouse.wheel', x, y, deltaX: event.deltaX, deltaY: event.deltaY })
  }

  function sendKeyDown(event) {
    event.preventDefault()
    _sendJSON({
      type: 'key.down',
      key: event.key,
      code: event.code,
      modifiers: _getModifiers(event),
      text: event.key.length === 1 ? event.key : '',
    })
    _resetIdleOnInput()
  }

  function sendKeyUp(event) {
    event.preventDefault()
    _sendJSON({
      type: 'key.up',
      key: event.key,
      code: event.code,
      modifiers: _getModifiers(event),
    })
  }

  // --- Idle Countdown ---

  function _startIdleCountdown(totalSeconds) {
    _stopIdleCountdown()
    idleTimeout.value = totalSeconds
    idleRemaining.value = totalSeconds
    _idleInterval = setInterval(() => {
      idleRemaining.value--
      if (idleRemaining.value <= 0) {
        _stopIdleCountdown()
      }
    }, 1000)
  }

  function _stopIdleCountdown() {
    if (_idleInterval) {
      clearInterval(_idleInterval)
      _idleInterval = null
    }
    idleTimeout.value = 0
    idleRemaining.value = 0
  }

  // --- Control ---

  function requestControl() {
    _sendJSON({ type: 'control.request', user_name: _userName })
  }

  function releaseControl() {
    _sendJSON({ type: 'control.release' })
  }

  function transferControl(toUserId) {
    _sendJSON({ type: 'control.transfer', to_user_id: toUserId })
  }

  function closeBrowser() {
    _sendJSON({ type: 'browser.close' })
  }

  // Cleanup on unmount
  onUnmounted(() => {
    _stopIdleCountdown()
    disconnect()
  })

  return {
    // State
    isConnected,
    isStreaming,
    viewerCount,
    hasControl,
    driverUserId,
    viewers,
    controlRequest,
    viewport,
    canvasRef,
    serverStopped,
    idleTimeout,
    idleRemaining,

    // Connection
    connect,
    disconnect,

    // Input handlers (attach to canvas events)
    sendMouseClick,
    sendMouseDown,
    sendMouseUp,
    sendMouseMove,
    sendWheel,
    sendKeyDown,
    sendKeyUp,

    // Control
    requestControl,
    releaseControl,
    transferControl,
    closeBrowser,
  }
}
