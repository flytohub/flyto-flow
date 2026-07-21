import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { getWsUrl } from '@/config/api'
import { DEFAULTS } from '@/config/defaults'
import { escapeHtml } from '@/services/domUtils'

/**
 * Composable for terminal log management with WebSocket connection
 * @param {Object} options - Options for the terminal
 * @param {import('vue').Ref<boolean>} options.show - Reactive ref for dialog visibility
 * @param {import('vue').Ref<HTMLElement|null>} options.terminalBody - Ref to terminal body element for scrolling
 */
export function useTerminalLogs(options = {}) {
  const { show, terminalBody } = options

  // State
  const logs = ref([])
  const searchQuery = ref('')
  const showSearch = ref(true)
  const autoScroll = ref(true)
  const isConnected = ref(false)
  const activeFilters = ref(['ERROR', 'WARNING', 'INFO', 'DEBUG'])
  const connectionStartTime = ref(null)
  const connectionTime = ref('00:00:00')

  // WebSocket instance
  let ws = null
  let connectionTimer = null
  let reconnectTimeout = null

  // Log levels config
  const levels = [
    { name: 'ERROR', icon: 'AlertCircle' },
    { name: 'WARNING', icon: 'AlertTriangle' },
    { name: 'INFO', icon: 'Info' },
    { name: 'DEBUG', icon: 'Bug' }
  ]

  // Filtered logs
  const filteredLogs = computed(() => {
    let result = logs.value.filter(log => activeFilters.value.includes(log.level))

    if (searchQuery.value.trim()) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(log =>
        log.message.toLowerCase().includes(query) ||
        log.logger.toLowerCase().includes(query)
      )
    }

    return result
  })

  // WebSocket connection
  function connectWebSocket() {
    // Resolve at connect time so the desktop sidecar's dynamic port is picked up.
    const wsUrl = `${getWsUrl()}/ws/logs`

    try {
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        isConnected.value = true
        connectionStartTime.value = Date.now()
        startConnectionTimer()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'log') {
            logs.value.push(data.data)
            // Limit logs to 1000 entries
            if (logs.value.length > 1000) {
              logs.value = logs.value.slice(-1000)
            }
            if (autoScroll.value) {
              scrollToBottom()
            }
          }
        } catch (e) {
          // Ignore parse errors
        }
      }

      ws.onerror = () => {
        // Error handling
      }

      ws.onclose = () => {
        isConnected.value = false
        stopConnectionTimer()
        // Clear any pending reconnect timeout
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout)
        }
        // Reconnect after delay
        reconnectTimeout = setTimeout(() => {
          reconnectTimeout = null
          if (show?.value) {
            connectWebSocket()
          }
        }, DEFAULTS.TIMING.RECONNECT_DELAY)
      }
    } catch (e) {
      // Connection error
    }
  }

  function disconnectWebSocket() {
    if (ws) {
      ws.close()
      ws = null
    }
    stopConnectionTimer()
  }

  function startConnectionTimer() {
    connectionTimer = setInterval(() => {
      if (connectionStartTime.value) {
        const elapsed = Math.floor((Date.now() - connectionStartTime.value) / 1000)
        const hours = String(Math.floor(elapsed / 3600)).padStart(2, '0')
        const minutes = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0')
        const seconds = String(elapsed % 60).padStart(2, '0')
        connectionTime.value = `${hours}:${minutes}:${seconds}`
      }
    }, 1000)
  }

  function stopConnectionTimer() {
    if (connectionTimer) {
      clearInterval(connectionTimer)
      connectionTimer = null
    }
  }

  // Formatting functions
  function formatTime(timestamp) {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  function formatLogger(logger) {
    const parts = logger.split('.')
    if (parts.length > 2) {
      return parts.slice(-2).join('.')
    }
    return logger
  }

  function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  }

  function highlightSearch(text) {
    if (!searchQuery.value.trim()) return escapeHtml(text)
    const escapedQuery = escapeRegExp(searchQuery.value)
    const regex = new RegExp(`(${escapedQuery})`, 'gi')
    return escapeHtml(text).replace(regex, '<mark>$1</mark>')
  }

  // Filter management
  function toggleFilter(level) {
    const index = activeFilters.value.indexOf(level)
    if (index > -1) {
      activeFilters.value.splice(index, 1)
    } else {
      activeFilters.value.push(level)
    }
  }

  // Auto-scroll management
  function toggleAutoScroll() {
    autoScroll.value = !autoScroll.value
    if (autoScroll.value) {
      scrollToBottom()
    }
  }

  async function scrollToBottom() {
    await nextTick()
    if (terminalBody?.value) {
      terminalBody.value.scrollTop = terminalBody.value.scrollHeight
    }
  }

  function handleScroll() {
    if (!terminalBody?.value) return
    const { scrollTop, scrollHeight, clientHeight } = terminalBody.value
    // Disable auto-scroll if user scrolls up
    if (scrollHeight - scrollTop - clientHeight > 50) {
      autoScroll.value = false
    }
  }

  // Clear logs
  function clearLogs() {
    logs.value = []
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send('clear')
    }
  }

  // Watch for show changes if provided
  if (show) {
    watch(show, (newVal) => {
      if (newVal) {
        connectWebSocket()
      } else {
        disconnectWebSocket()
      }
    })

    onMounted(() => {
      if (show.value) {
        connectWebSocket()
      }
    })
  }

  onUnmounted(() => {
    // Clear reconnect timeout to prevent memory leak
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
    disconnectWebSocket()
  })

  return {
    // State
    logs,
    searchQuery,
    showSearch,
    autoScroll,
    isConnected,
    activeFilters,
    connectionTime,

    // Config
    levels,

    // Computed
    filteredLogs,

    // Methods
    formatTime,
    formatLogger,
    highlightSearch,
    toggleFilter,
    toggleAutoScroll,
    clearLogs,
    handleScroll,
    connectWebSocket,
    disconnectWebSocket
  }
}
