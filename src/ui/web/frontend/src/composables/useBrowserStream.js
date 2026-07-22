/** Same-origin browser screencast for the single local workspace. */
import { onUnmounted, ref } from 'vue'
import { getWsUrl } from '@/config/api'
import { DEFAULTS } from '@/config/defaults'

export function useBrowserStream(executionId) {
  const isConnected = ref(false)
  const isStreaming = ref(false)
  const viewport = ref({ width: 1280, height: 720 })
  const canvasRef = ref(null)
  const serverStopped = ref(false)
  const idleTimeout = ref(0)
  const idleRemaining = ref(0)

  let ws = null
  let reconnectTimeout = null
  let reconnectAttempts = 0
  let idleInterval = null
  let latestBitmap = null
  let rafId = null
  let decoding = false
  let nextBuffer = null
  let context = null

  function resolveExecutionId() {
    return typeof executionId === 'object' && executionId.value !== undefined
      ? executionId.value
      : executionId
  }

  function connect() {
    serverStopped.value = false
    reconnectAttempts = 0
    openSocket()
  }

  function openSocket() {
    disconnect(false)
    const id = resolveExecutionId()
    if (!id) return

    ws = new WebSocket(`${getWsUrl()}/ws/browser/${id}`)
    ws.binaryType = 'arraybuffer'
    ws.onopen = () => {
      isConnected.value = true
      reconnectAttempts = 0
    }
    ws.onmessage = event => {
      if (event.data instanceof ArrayBuffer) {
        isStreaming.value = true
        renderFrame(event.data)
        return
      }
      try {
        handleMessage(JSON.parse(event.data))
      } catch {
        // Ignore malformed local runtime events.
      }
    }
    ws.onclose = () => {
      isConnected.value = false
      isStreaming.value = false
      scheduleReconnect()
    }
  }

  function disconnect(stopReconnect = true) {
    if (reconnectTimeout) clearTimeout(reconnectTimeout)
    reconnectTimeout = null
    if (stopReconnect) reconnectAttempts = DEFAULTS.WEBSOCKET.MAX_RECONNECT_ATTEMPTS
    if (ws) {
      ws.onclose = null
      ws.close()
      ws = null
    }
    isConnected.value = false
    isStreaming.value = false
    if (rafId) cancelAnimationFrame(rafId)
    if (latestBitmap) latestBitmap.close()
    rafId = null
    latestBitmap = null
    nextBuffer = null
    decoding = false
    context = null
  }

  function scheduleReconnect() {
    const maximum = DEFAULTS.WEBSOCKET.MAX_RECONNECT_ATTEMPTS
    if (reconnectAttempts >= maximum) return
    reconnectAttempts += 1
    reconnectTimeout = setTimeout(
      openSocket,
      DEFAULTS.WEBSOCKET.RECONNECT_INTERVAL * reconnectAttempts
    )
  }

  function handleMessage(message) {
    if (message.type === 'screencast.started') {
      isStreaming.value = true
      serverStopped.value = false
      if (message.viewport) viewport.value = message.viewport
    } else if (message.type === 'screencast.stopped') {
      isStreaming.value = false
      serverStopped.value = true
      stopIdleCountdown()
    } else if (message.type === 'browser_idle') {
      startIdleCountdown(message.timeout_seconds || 300)
    }
  }

  function renderFrame(buffer) {
    nextBuffer = buffer
    if (!decoding) decodeNext()
  }

  function decodeNext() {
    if (!nextBuffer) return
    const buffer = nextBuffer
    nextBuffer = null
    decoding = true
    createImageBitmap(new Blob([buffer], { type: 'image/jpeg' }))
      .then(bitmap => {
        if (latestBitmap) latestBitmap.close()
        latestBitmap = bitmap
        if (!rafId) rafId = requestAnimationFrame(paint)
      })
      .finally(() => {
        decoding = false
        decodeNext()
      })
  }

  function paint() {
    rafId = null
    const canvas = canvasRef.value
    if (!canvas || !latestBitmap) return
    if (canvas.width !== viewport.value.width || canvas.height !== viewport.value.height) {
      canvas.width = viewport.value.width
      canvas.height = viewport.value.height
      context = null
    }
    context ||= canvas.getContext('2d', { alpha: false, desynchronized: true })
    context.drawImage(latestBitmap, 0, 0, canvas.width, canvas.height)
  }

  function send(message) {
    if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify(message))
  }

  function coordinates(event) {
    const canvas = canvasRef.value
    if (!canvas) return { x: 0, y: 0 }
    return {
      x: Math.round(event.offsetX * viewport.value.width / canvas.clientWidth),
      y: Math.round(event.offsetY * viewport.value.height / canvas.clientHeight)
    }
  }

  function buttonName(button) {
    return button === 1 ? 'middle' : button === 2 ? 'right' : 'left'
  }

  function modifiers(event) {
    return (event.altKey ? 1 : 0) |
      (event.ctrlKey ? 2 : 0) |
      (event.metaKey ? 4 : 0) |
      (event.shiftKey ? 8 : 0)
  }

  function resetIdleOnInput() {
    if (idleRemaining.value > 0) stopIdleCountdown()
  }

  function sendMouseDown(event) {
    send({ type: 'mouse.down', ...coordinates(event), button: buttonName(event.button) })
    resetIdleOnInput()
  }
  function sendMouseUp(event) {
    send({ type: 'mouse.up', ...coordinates(event), button: buttonName(event.button) })
  }
  function sendMouseMove(event) { send({ type: 'mouse.move', ...coordinates(event) }) }
  function sendWheel(event) {
    send({ type: 'mouse.wheel', ...coordinates(event), deltaX: event.deltaX, deltaY: event.deltaY })
    resetIdleOnInput()
  }
  function sendKeyDown(event) {
    event.preventDefault()
    send({
      type: 'key.down', key: event.key, code: event.code,
      modifiers: modifiers(event), text: event.key.length === 1 ? event.key : ''
    })
    resetIdleOnInput()
  }
  function sendKeyUp(event) {
    event.preventDefault()
    send({ type: 'key.up', key: event.key, code: event.code, modifiers: modifiers(event) })
  }
  function closeBrowser() { send({ type: 'browser.close' }) }

  function startIdleCountdown(seconds) {
    stopIdleCountdown()
    idleTimeout.value = seconds
    idleRemaining.value = seconds
    idleInterval = setInterval(() => {
      idleRemaining.value -= 1
      if (idleRemaining.value <= 0) stopIdleCountdown()
    }, 1000)
  }

  function stopIdleCountdown() {
    if (idleInterval) clearInterval(idleInterval)
    idleInterval = null
    idleTimeout.value = 0
    idleRemaining.value = 0
  }

  onUnmounted(() => {
    stopIdleCountdown()
    disconnect()
  })

  return {
    isConnected, isStreaming, viewport, canvasRef, serverStopped,
    idleTimeout, idleRemaining, connect, disconnect, sendMouseDown,
    sendMouseUp, sendMouseMove, sendWheel, sendKeyDown, sendKeyUp, closeBrowser
  }
}
