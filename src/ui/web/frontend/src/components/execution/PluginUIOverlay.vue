<template>
  <!--
    Plugin UI Overlay
    Appears when a plugin step requests a UI interaction during workflow execution.
    Triggered by WebSocket event: plugin_ui_open
  -->
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="plugin-ui-overlay"
      @click.self="handleBackdropClick"
    >
      <div
        class="plugin-ui-dialog"
        :style="dialogStyle"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
      >
        <!-- Header -->
        <div class="plugin-ui-header">
          <div class="plugin-ui-title">
            <div class="plugin-ui-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2v6m0 12v2M4.93 4.93l4.24 4.24m5.66 5.66l4.24 4.24M2 12h6m12 0h2M4.93 19.07l4.24-4.24m5.66-5.66l4.24-4.24"/>
              </svg>
            </div>
            <span>{{ title }}</span>
          </div>
          <button class="plugin-ui-close" @click="handleClose" aria-label="Close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- iframe -->
        <div class="plugin-ui-body">
          <iframe
            v-if="iframeUrl"
            ref="iframeRef"
            :src="iframeUrl"
            class="plugin-ui-iframe"
            sandbox="allow-scripts allow-forms allow-popups"
            allow="clipboard-write"
            @load="onIframeLoad"
          />
          <div v-else class="plugin-ui-loading">
            <div class="plugin-ui-spinner" />
            <span>Loading plugin UI...</span>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const FLYTO_MSG_PREFIX = 'flyto-plugin:'

const isOpen = ref(false)
const iframeUrl = ref('')
const pluginId = ref('')
const requestId = ref('')
const uiType = ref('dialog')
const uiWidth = ref(720)
const uiHeight = ref(600)
const title = ref('Plugin')
const iframeRef = ref(null)

const dialogStyle = computed(() => ({
  width: `${uiWidth.value}px`,
  maxWidth: '95vw',
  height: uiType.value === 'page' ? '95vh' : `${uiHeight.value}px`,
  maxHeight: '95vh',
}))

// ── WebSocket event listener ────────────────────────────
function handleWsMessage(event) {
  // Listen for CustomEvent dispatched from execution WS handler
  if (!event.detail) return
  const data = event.detail

  if (data.type === 'plugin_ui_open') {
    iframeUrl.value = data.url || ''
    pluginId.value = data.plugin_id || ''
    requestId.value = data.requestId || ''
    uiType.value = data.uiType || data.type_hint || 'dialog'
    uiWidth.value = data.width || 720
    uiHeight.value = data.height || 600
    title.value = data.title || data.plugin_id || 'Plugin'
    isOpen.value = true
  }

  if (data.type === 'plugin_ui_close') {
    if (data.requestId === requestId.value || !data.requestId) {
      close()
    }
  }
}

// ── postMessage listener (backup communication channel) ──
function handlePostMessage(event) {
  // Security: only accept messages from the plugin iframe's own origin
  if (event.origin && iframeUrl.value) {
    try {
      const expected = new URL(iframeUrl.value).origin
      if (event.origin !== expected) return
    } catch { return }
  }

  if (typeof event.data !== 'string') return
  if (!event.data.startsWith(FLYTO_MSG_PREFIX)) return

  try {
    const payload = JSON.parse(event.data.slice(FLYTO_MSG_PREFIX.length))

    if (payload.type === 'submit' || payload.type === 'cancel') {
      // The plugin SDK's HTTP callback handles the actual data flow.
      // When the UI submits/cancels, the plugin process will eventually
      // send ui.close via JSON-RPC → WS, which closes this overlay.
      // But as a fast path, close immediately on postMessage.
      close()
    }
  } catch {
    // ignore
  }
}

function onIframeLoad() {
  // Send theme tokens to the iframe
  if (iframeRef.value?.contentWindow) {
    const tokens = getComputedThemeTokens()
    iframeRef.value.contentWindow.postMessage(
      FLYTO_MSG_PREFIX + JSON.stringify({ type: 'theme', data: tokens }),
      '*'
    )
  }
}

function getComputedThemeTokens() {
  const style = getComputedStyle(document.documentElement)
  const tokens = {}
  const prefixes = ['--flyto-']
  // Extract a subset of commonly used tokens
  const keys = [
    '--flyto-primary', '--flyto-primary-light', '--flyto-primary-dark',
    '--flyto-accent', '--flyto-success', '--flyto-warning', '--flyto-error',
    '--flyto-bg-page', '--flyto-bg-card', '--flyto-bg-card-solid', '--flyto-bg-input',
    '--flyto-border', '--flyto-border-strong',
    '--flyto-text-primary', '--flyto-text-secondary', '--flyto-text-tertiary',
  ]
  for (const key of keys) {
    const val = style.getPropertyValue(key).trim()
    if (val) tokens[key] = val
  }
  return tokens
}

function handleClose() {
  // Notify the iframe we're closing (it may need to cancel)
  if (iframeRef.value?.contentWindow) {
    iframeRef.value.contentWindow.postMessage(
      FLYTO_MSG_PREFIX + JSON.stringify({ type: 'host_close' }),
      '*'
    )
  }
  close()
}

function handleBackdropClick() {
  // Don't close on backdrop click for plugin UIs — user might lose work
}

function close() {
  isOpen.value = false
  iframeUrl.value = ''
  requestId.value = ''
}

onMounted(() => {
  window.addEventListener('flyto-plugin-ui', handleWsMessage)
  window.addEventListener('message', handlePostMessage)
})

onUnmounted(() => {
  window.removeEventListener('flyto-plugin-ui', handleWsMessage)
  window.removeEventListener('message', handlePostMessage)
})
</script>

<style scoped>
.plugin-ui-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

.plugin-ui-dialog {
  background: var(--flyto-bg-card-solid, #1e293b);
  border: 1px solid var(--flyto-border, rgba(148, 163, 184, 0.1));
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.plugin-ui-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid var(--flyto-border, rgba(148, 163, 184, 0.1));
  flex-shrink: 0;
}

.plugin-ui-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--flyto-text-primary, #f1f5f9);
}

.plugin-ui-icon {
  width: 16px;
  height: 16px;
  color: var(--flyto-primary, #8b5cf6);
}

.plugin-ui-icon svg {
  width: 100%;
  height: 100%;
}

.plugin-ui-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: var(--flyto-text-tertiary, #64748b);
  transition: all 0.15s ease;
}

.plugin-ui-close:hover {
  background: var(--flyto-bg-hover, rgba(148, 163, 184, 0.08));
  color: var(--flyto-text-primary, #f1f5f9);
}

.plugin-ui-close svg {
  width: 16px;
  height: 16px;
}

.plugin-ui-body {
  flex: 1;
  overflow: hidden;
}

.plugin-ui-iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.plugin-ui-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 100%;
  color: var(--flyto-text-secondary, #94a3b8);
  font-size: 13px;
}

.plugin-ui-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--flyto-border-strong, rgba(148, 163, 184, 0.2));
  border-top-color: var(--flyto-primary, #8b5cf6);
  border-radius: 50%;
  animation: plugin-spin 0.8s linear infinite;
}

@keyframes plugin-spin {
  to { transform: rotate(360deg); }
}
</style>
