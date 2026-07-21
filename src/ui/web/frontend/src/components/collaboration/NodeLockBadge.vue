<template>
  <Transition name="fade">
    <div
      v-if="lock"
      class="node-lock-badge"
      :class="{ 'is-own-lock': isOwnLock }"
      :style="{ '--lock-color': lockColor }"
      :title="lockTitle"
    >
      <Lock :size="12" />
      <span v-if="showName" class="lock-owner">{{ lock.userName }}</span>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'
import { Lock } from 'lucide-vue-next'
import { useCollaborationStore } from '@/stores/collaborationStore'
import { storeToRefs } from 'pinia'

const props = defineProps({
  nodeId: {
    type: String,
    required: true
  },
  showName: {
    type: Boolean,
    default: false
  }
})

const collaborationStore = useCollaborationStore()
const { nodeLocks } = storeToRefs(collaborationStore)

const lock = computed(() => {
  return nodeLocks.value[props.nodeId] || null
})

const isOwnLock = computed(() => {
  return collaborationStore.hasLockOn(props.nodeId)
})

const lockColor = computed(() => {
  if (!lock.value) return '#64748b'
  // Get participant color from collaboration store
  const participant = collaborationStore.participants.find(
    p => p.userId === lock.value.userId || p.user_id === lock.value.userId
  )
  return participant?.color || '#8b5cf6'
})

const lockTitle = computed(() => {
  if (!lock.value) return ''
  if (isOwnLock.value) {
    return 'You are editing this node'
  }
  return `Locked by ${lock.value.userName}`
})
</script>

<style scoped>
.node-lock-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid var(--lock-color);
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  color: var(--lock-color);
  backdrop-filter: blur(4px);
  white-space: nowrap;
  pointer-events: auto;
  cursor: default;
}

.node-lock-badge.is-own-lock {
  background: rgba(34, 197, 94, 0.15);
  border-color: #22c55e;
  color: #22c55e;
}

.lock-owner {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
