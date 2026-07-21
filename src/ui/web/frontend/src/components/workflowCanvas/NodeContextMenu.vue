<template>
  <Teleport to="body">
    <Transition name="context-menu">
      <div
        v-if="visible"
        ref="menuRef"
        class="fixed z-[9999] min-w-[200px] py-1.5 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl shadow-black/40"
        :style="{ left: `${position.x}px`, top: `${position.y}px` }"
        @contextmenu.prevent
      >
        <!-- Save as Template -->
        <button
          class="context-menu-item"
          @click="handleSaveAsTemplate"
        >
          <BookTemplate :size="16" class="text-purple-400" />
          <span>{{ $t('workflow.saveAsTemplate', 'Save as Template') }}</span>
        </button>

        <!-- Duplicate -->
        <button
          class="context-menu-item"
          @click="handleDuplicate"
        >
          <Copy :size="16" class="text-blue-400" />
          <span>{{ $t('workflow.duplicateNode', 'Duplicate') }}</span>
        </button>

        <div class="border-t border-gray-700 my-1"></div>

        <!-- Disable/Enable -->
        <button
          class="context-menu-item"
          @click="handleToggleDisabled"
        >
          <CircleSlash v-if="!isDisabled" :size="16" class="text-yellow-400" />
          <CirclePlay v-else :size="16" class="text-green-400" />
          <span>{{ isDisabled ? $t('workflow.enable', 'Enable') : $t('workflow.disable', 'Disable') }}</span>
        </button>

        <div class="border-t border-gray-700 my-1"></div>

        <!-- Delete -->
        <button
          class="context-menu-item text-red-400 hover:bg-red-500/10"
          @click="handleDelete"
        >
          <Trash2 :size="16" />
          <span>{{ $t('debug.checkpoint.deleteNode', 'Delete') }}</span>
        </button>
      </div>
    </Transition>

    <!-- Invisible backdrop to close menu -->
    <div
      v-if="visible"
      class="fixed inset-0 z-[9998]"
      @click="close"
      @contextmenu.prevent="close"
    />
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { BookTemplate, Copy, CircleSlash, CirclePlay, Trash2 } from 'lucide-vue-next'

const props = defineProps({
  visible: { type: Boolean, default: false },
  position: { type: Object, default: () => ({ x: 0, y: 0 }) },
  node: { type: Object, default: null }
})

const emit = defineEmits(['close', 'save-as-template', 'duplicate', 'toggle-disabled', 'delete'])

const menuRef = ref(null)

const isDisabled = ref(false)

watch(() => props.node, (node) => {
  isDisabled.value = node?.data?.disabled || false
})

// Adjust menu position to stay within viewport
watch(() => props.visible, async (val) => {
  if (!val) return
  await nextTick()
  if (!menuRef.value) return

  const rect = menuRef.value.getBoundingClientRect()
  const vw = window.innerWidth
  const vh = window.innerHeight

  if (rect.right > vw) {
    menuRef.value.style.left = `${vw - rect.width - 8}px`
  }
  if (rect.bottom > vh) {
    menuRef.value.style.top = `${vh - rect.height - 8}px`
  }
})

function close() {
  emit('close')
}

function handleSaveAsTemplate() {
  emit('save-as-template', props.node)
  close()
}

function handleDuplicate() {
  emit('duplicate', props.node)
  close()
}

function handleToggleDisabled() {
  emit('toggle-disabled', props.node?.id)
  close()
}

function handleDelete() {
  emit('delete', props.node?.id)
  close()
}

// Close on Escape
function onKeydown(e) {
  if (e.key === 'Escape') close()
}

watch(() => props.visible, (val) => {
  if (val) {
    document.addEventListener('keydown', onKeydown)
  } else {
    document.removeEventListener('keydown', onKeydown)
  }
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.context-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 14px;
  font-size: 13px;
  color: #e2e8f0;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s;
  border: none;
  background: none;
}

.context-menu-item:hover {
  background: rgba(139, 92, 246, 0.15);
}

.context-menu-enter-active {
  transition: all 0.15s ease-out;
}
.context-menu-leave-active {
  transition: all 0.1s ease-in;
}
.context-menu-enter-from {
  opacity: 0;
  transform: scale(0.95);
}
.context-menu-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
