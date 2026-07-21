<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-[1100] flex items-center justify-center bg-black/60"
    @click.self="$emit('close')"
  >
    <div class="w-full max-w-5xl h-[85vh] bg-gray-900 rounded-xl shadow-2xl overflow-hidden flex flex-col">
      <!-- Header / Toolbar -->
      <div class="flex items-center justify-between px-4 py-2 border-b border-gray-700 bg-gray-800 shrink-0">
        <div class="flex items-center gap-3">
          <div class="p-1.5 bg-blue-600/20 rounded-lg">
            <Globe :size="20" class="text-blue-400" />
          </div>
          <span class="text-sm font-medium text-white">{{ $t('browser.liveView', 'Live Browser') }}</span>

          <!-- Connection status -->
          <span
            class="w-2 h-2 rounded-full"
            :class="isConnected ? 'bg-green-400' : 'bg-red-400'"
          />

          <!-- Viewer count -->
          <span v-if="viewerCount > 0" class="text-xs text-gray-400 flex items-center gap-1">
            <Eye :size="14" />
            {{ viewerCount }}
          </span>
        </div>

        <div class="flex items-center gap-2">
          <!-- Cloud mode: view-only indicator -->
          <template v-if="cloudMode">
            <span class="text-xs text-gray-400 flex items-center gap-1">
              <Eye :size="14" />
              {{ $t('browser.viewOnly', 'View Only') }}
            </span>
          </template>

          <!-- Desktop mode: full control -->
          <template v-else>
            <!-- Driver seat indicator -->
            <span v-if="hasControl" class="text-xs text-green-400 flex items-center gap-1">
              <MousePointer :size="14" />
              {{ $t('browser.controlling', 'Controlling') }}
            </span>
            <span v-else class="text-xs text-gray-500 flex items-center gap-1">
              <Eye :size="14" />
              {{ $t('browser.viewing', 'Viewing') }}
            </span>

            <!-- Request / Release control -->
            <button
              v-if="!hasControl"
              @click="requestControl"
              class="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors"
              aria-label="Request control"
            >
              {{ $t('browser.requestControl', 'Request Control') }}
            </button>
            <button
              v-else
              @click="releaseControl"
              class="px-2 py-1 text-xs bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors"
              aria-label="Release control"
            >
              {{ $t('browser.releaseControl', 'Release') }}
            </button>

            <!-- Close browser (kill) -->
            <button
              @click="closeBrowser"
              class="px-2 py-1 text-xs bg-red-600/80 hover:bg-red-500 text-white rounded transition-colors flex items-center gap-1"
              :title="$t('browser.closeBrowser', 'Close Browser')"
              aria-label="Close browser"
            >
              <Power :size="14" />
            </button>
          </template>

          <!-- Hide dialog -->
          <button
            @click="$emit('close')"
            class="p-1 text-gray-400 hover:text-white transition-colors"
            aria-label="Close"
          >
            <X :size="20" />
          </button>
        </div>
      </div>

      <!-- Control request notification (desktop only) -->
      <div
        v-if="!cloudMode && controlRequest && hasControl"
        class="flex items-center justify-between px-4 py-2 bg-yellow-900/30 border-b border-yellow-700/50 shrink-0"
      >
        <span class="text-xs text-yellow-300">
          {{ controlRequest.user_name }} {{ $t('browser.requestsControl', 'requests control') }}
        </span>
        <div class="flex gap-2">
          <button
            @click="grantControl"
            class="px-2 py-0.5 text-xs bg-green-600 hover:bg-green-500 text-white rounded"
            aria-label="Grant control"
          >
            {{ $t('browser.grant', 'Grant') }}
          </button>
          <button
            @click="controlRequest = null"
            class="px-2 py-0.5 text-xs bg-gray-600 hover:bg-gray-500 text-white rounded"
            aria-label="Deny control"
          >
            {{ $t('browser.deny', 'Deny') }}
          </button>
        </div>
      </div>

      <!-- Idle countdown bar -->
      <div
        v-if="idleRemaining > 0"
        class="shrink-0 px-4 py-2 bg-amber-900/40 border-b border-amber-700/50 flex items-center gap-3"
      >
        <div class="flex-1">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs text-amber-300">
              {{ $t('browser.idleWarning', 'Browser will close in') }}
              {{ Math.floor(idleRemaining / 60) }}:{{ String(idleRemaining % 60).padStart(2, '0') }}
            </span>
            <span class="text-xs text-amber-400/60">
              {{ $t('browser.interactToKeep', 'Interact to reset timer') }}
            </span>
          </div>
          <div class="w-full h-1 bg-amber-900/60 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-1000 ease-linear"
              :class="idleRemaining < 60 ? 'bg-red-500' : 'bg-amber-400'"
              :style="{ width: `${(idleRemaining / idleTimeout) * 100}%` }"
            />
          </div>
        </div>
      </div>

      <!-- Canvas area -->
      <div class="flex-1 relative overflow-hidden bg-black flex items-start justify-center">
        <!-- Loading state -->
        <div
          v-if="!isStreaming"
          class="absolute inset-0 flex flex-col items-center justify-center gap-3 z-10"
        >
          <Loader v-if="isConnected" :size="32" class="text-blue-400 animate-spin" />
          <Globe v-else :size="48" class="text-gray-600" />
          <span class="text-sm text-gray-400">
            {{ isConnected
              ? $t('browser.waitingForStream', 'Waiting for browser...')
              : $t('browser.connecting', 'Connecting...')
            }}
          </span>
        </div>

        <!-- Browser canvas -->
        <canvas
          ref="canvasRef"
          tabindex="0"
          class="max-w-full max-h-full outline-none"
          :class="{ 'cursor-pointer': hasControl, 'cursor-default': !hasControl }"
          :style="canvasStyle"
          @mousedown.prevent="onMouseDown"
          @mouseup.prevent="onMouseUp"
          @mousemove="onMouseMove"
          @wheel.prevent="onWheel"
          @keydown="onKeyDown"
          @keyup="onKeyUp"
          @contextmenu.prevent
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch, onMounted, toRef } from 'vue'
import { Globe, Eye, MousePointer, X, Loader, Power } from 'lucide-vue-next'
// Monitor removed — using Globe for all browser icons
import { useBrowserStream } from '@/composables/useBrowserStream'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  executionId: { type: String, required: true },
  userId: { type: String, default: '' },
  userName: { type: String, default: 'Anonymous' },
  cloudMode: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'browser-closed'])

// Pass as ref so composable tracks prop changes
const {
  isConnected,
  isStreaming,
  viewerCount,
  hasControl,
  driverUserId,
  controlRequest,
  viewport,
  canvasRef,
  serverStopped,
  idleTimeout,
  idleRemaining,
  connect,
  disconnect,
  sendMouseDown,
  sendMouseUp,
  sendMouseMove,
  sendWheel,
  sendKeyDown,
  sendKeyUp,
  requestControl,
  releaseControl,
  transferControl,
  closeBrowser,
} = useBrowserStream(toRef(props, 'executionId'), { cloudMode: props.cloudMode })

const canvasStyle = computed(() => {
  const ratio = viewport.value.width / viewport.value.height
  return {
    aspectRatio: `${ratio}`,
  }
})

function grantControl() {
  if (controlRequest.value) {
    transferControl(controlRequest.value.user_id)
    controlRequest.value = null
  }
}

// Input handlers — only forward if we have control
function onMouseDown(e) {
  if (!hasControl.value) return
  canvasRef.value?.focus()
  sendMouseDown(e)
}

function onMouseUp(e) {
  if (!hasControl.value) return
  sendMouseUp(e)
}

let _moveThrottle = 0
function onMouseMove(e) {
  if (!hasControl.value) return
  const now = Date.now()
  if (now - _moveThrottle < 32) return // throttle to ~30fps
  _moveThrottle = now
  sendMouseMove(e)
}

function onWheel(e) {
  if (!hasControl.value) return
  sendWheel(e)
}

function onKeyDown(e) {
  if (!hasControl.value) return
  sendKeyDown(e)
}

function onKeyUp(e) {
  if (!hasControl.value) return
  sendKeyUp(e)
}

// Connect/disconnect based on isOpen
watch(() => props.isOpen, (open) => {
  if (open) {
    connect(props.userId, props.userName)
  } else {
    disconnect()
  }
})

// When server stops screencast (browser.close), notify parent
watch(serverStopped, (stopped) => {
  if (stopped) {
    emit('browser-closed')
  }
})

// Auto-connect if initially open
onMounted(() => {
  if (props.isOpen) {
    connect(props.userId, props.userName)
  }
})
</script>
