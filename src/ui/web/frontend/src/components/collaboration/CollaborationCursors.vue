<template>
  <div class="collab-cursors-overlay">
    <div
      class="collab-viewport-wrapper"
      :style="{ transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.zoom})`, transformOrigin: '0 0' }"
    >
      <div
        v-for="(cursor, pid) in otherCursors"
        :key="pid"
        class="collab-cursor"
        :class="{ 'is-idle': isIdle(cursor), 'is-hidden': isHidden(cursor) }"
        :style="{ transform: `translate(${cursor.x}px, ${cursor.y}px)` }"
      >
        <!-- Arrow SVG -->
        <svg width="18" height="22" viewBox="0 0 18 22" fill="none" class="collab-cursor-arrow">
          <path
            d="M1.5 1L16 11L9 12.5L5.5 21L1.5 1Z"
            :fill="cursor.color"
            stroke="#000"
            stroke-width="1.2"
            stroke-linejoin="round"
          />
        </svg>
        <!-- Name label -->
        <div class="collab-cursor-label" :style="{ borderColor: cursor.color }">
          {{ cursor.displayName }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useCollaborationStore } from '@/stores/collaborationStore'
import { storeToRefs } from 'pinia'

defineProps({
  viewport: {
    type: Object,
    required: true,
  }
})

const collaborationStore = useCollaborationStore()
const { otherCursors } = storeToRefs(collaborationStore)

const IDLE_MS = 3000
const HIDDEN_MS = 10000

// Reactive tick to force re-evaluation of idle/hidden classes
const now = ref(Date.now())

function isIdle(cursor) {
  if (!cursor.lastUpdate) return false
  const elapsed = now.value - cursor.lastUpdate
  return elapsed >= IDLE_MS && elapsed < HIDDEN_MS
}

function isHidden(cursor) {
  if (!cursor.lastUpdate) return false
  return now.value - cursor.lastUpdate >= HIDDEN_MS
}

let idleTimer = null
onMounted(() => {
  idleTimer = setInterval(() => { now.value = Date.now() }, 1000)
})

onUnmounted(() => {
  if (idleTimer) clearInterval(idleTimer)
})
</script>

<style scoped>
.collab-cursors-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 50;
  overflow: hidden;
}

.collab-viewport-wrapper {
  width: 0;
  height: 0;
  will-change: transform;
}

.collab-cursor {
  position: absolute;
  top: 0;
  left: 0;
  will-change: transform, opacity;
  transition: transform 120ms ease-out, opacity 300ms ease;
  opacity: 1;
}

.collab-cursor.is-idle {
  opacity: 0.35;
}

.collab-cursor.is-hidden {
  opacity: 0;
}

.collab-cursor-arrow {
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.5));
}

.collab-cursor-label {
  position: absolute;
  top: 18px;
  left: 12px;
  padding: 2px 6px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  border: 1.5px solid;
  border-radius: 4px;
  white-space: nowrap;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}
</style>
