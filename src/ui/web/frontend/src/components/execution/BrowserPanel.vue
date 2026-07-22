<template>
  <div v-if="isOpen" class="fixed inset-0 z-[1100] flex items-center justify-center bg-black/60" @click.self="$emit('close')">
    <div class="flex h-[85vh] w-full max-w-5xl flex-col overflow-hidden rounded-xl bg-gray-900 shadow-2xl">
      <div class="flex shrink-0 items-center justify-between border-b border-gray-700 bg-gray-800 px-4 py-2">
        <div class="flex items-center gap-3">
          <Globe :size="20" class="text-blue-400" />
          <span class="text-sm font-medium text-white">{{ $t('browser.liveView', 'Local Browser') }}</span>
          <span class="h-2 w-2 rounded-full" :class="isConnected ? 'bg-green-400' : 'bg-red-400'" />
          <span class="flex items-center gap-1 text-xs text-green-400">
            <MousePointer :size="14" />
            {{ $t('browser.controlling', 'Local control') }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <button class="flex items-center gap-1 rounded bg-red-600/80 px-2 py-1 text-xs text-white hover:bg-red-500" aria-label="Close browser" @click="closeBrowser">
            <Power :size="14" />
          </button>
          <button class="p-1 text-gray-400 hover:text-white" aria-label="Close" @click="$emit('close')">
            <X :size="20" />
          </button>
        </div>
      </div>

      <div v-if="idleRemaining > 0" class="flex shrink-0 items-center gap-3 border-b border-amber-700/50 bg-amber-900/40 px-4 py-2">
        <div class="flex-1">
          <div class="mb-1 flex items-center justify-between text-xs text-amber-300">
            <span>Browser closes in {{ Math.floor(idleRemaining / 60) }}:{{ String(idleRemaining % 60).padStart(2, '0') }}</span>
            <span>Interact to keep it open</span>
          </div>
          <div class="h-1 overflow-hidden rounded-full bg-amber-900/60">
            <div class="h-full rounded-full bg-amber-400 transition-all duration-1000" :style="{ width: `${(idleRemaining / idleTimeout) * 100}%` }" />
          </div>
        </div>
      </div>

      <div class="relative flex flex-1 items-start justify-center overflow-hidden bg-black">
        <div v-if="!isStreaming" class="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3">
          <Loader v-if="isConnected" :size="32" class="animate-spin text-blue-400" />
          <Globe v-else :size="48" class="text-gray-600" />
          <span class="text-sm text-gray-400">{{ isConnected ? 'Waiting for local browser…' : 'Connecting…' }}</span>
        </div>
        <canvas
          ref="canvasRef"
          tabindex="0"
          class="max-h-full max-w-full cursor-pointer outline-none"
          :style="canvasStyle"
          @mousedown.prevent="onMouseDown"
          @mouseup.prevent="sendMouseUp"
          @mousemove="onMouseMove"
          @wheel.prevent="sendWheel"
          @keydown="sendKeyDown"
          @keyup="sendKeyUp"
          @contextmenu.prevent
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, toRef, watch } from 'vue'
import { Globe, Loader, MousePointer, Power, X } from 'lucide-vue-next'
import { useBrowserStream } from '@/composables/useBrowserStream'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  executionId: { type: String, required: true }
})
const emit = defineEmits(['close', 'browser-closed'])

const {
  isConnected, isStreaming, viewport, canvasRef, serverStopped,
  idleTimeout, idleRemaining, connect, disconnect, sendMouseDown,
  sendMouseUp, sendMouseMove, sendWheel, sendKeyDown, sendKeyUp, closeBrowser
} = useBrowserStream(toRef(props, 'executionId'))

const canvasStyle = computed(() => ({ aspectRatio: `${viewport.value.width / viewport.value.height}` }))

function onMouseDown(event) {
  canvasRef.value?.focus()
  sendMouseDown(event)
}

let lastMove = 0
function onMouseMove(event) {
  const now = Date.now()
  if (now - lastMove < 32) return
  lastMove = now
  sendMouseMove(event)
}

watch(() => props.isOpen, open => open ? connect() : disconnect())
watch(serverStopped, stopped => { if (stopped) emit('browser-closed') })
onMounted(() => { if (props.isOpen) connect() })
</script>
