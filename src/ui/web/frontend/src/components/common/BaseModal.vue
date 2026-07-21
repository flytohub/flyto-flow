<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="show"
        class="modal-overlay"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="title ? 'modal-title' : undefined"
        @click="handleOverlayClick"
        @keydown.esc="handleClose"
      >
        <div
          ref="modalRef"
          class="modal-container"
          :class="sizeClass"
          tabindex="-1"
          @click.stop
        >
          <div v-if="showHeader" class="modal-header">
            <slot name="header">
              <h3 id="modal-title" class="modal-title">{{ title }}</h3>
            </slot>
            <button
              v-if="showClose"
              type="button"
              class="modal-close"
              :aria-label="t('accessibility.closeModal')"
              @click="handleClose"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <div class="modal-body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="modal-footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: ''
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg', 'xl', 'full'].includes(v)
  },
  showHeader: {
    type: Boolean,
    default: true
  },
  showClose: {
    type: Boolean,
    default: true
  },
  closeOnOverlay: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['close'])

const modalRef = ref(null)
const previousActiveElement = ref(null)

const sizeClass = computed(() => `modal-${props.size}`)

// Focus trap: get all focusable elements
function getFocusableElements() {
  if (!modalRef.value) return []
  return modalRef.value.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
}

// Handle tab key for focus trap
function handleTabKey(e) {
  const focusable = getFocusableElements()
  if (focusable.length === 0) return

  const firstElement = focusable[0]
  const lastElement = focusable[focusable.length - 1]

  if (e.shiftKey && document.activeElement === firstElement) {
    e.preventDefault()
    lastElement.focus()
  } else if (!e.shiftKey && document.activeElement === lastElement) {
    e.preventDefault()
    firstElement.focus()
  }
}

// Lock body scroll when modal is open
function lockBodyScroll() {
  document.body.style.overflow = 'hidden'
}

function unlockBodyScroll() {
  document.body.style.overflow = ''
}

// Watch for show changes to manage focus
watch(() => props.show, async (newVal) => {
  if (newVal) {
    previousActiveElement.value = document.activeElement
    lockBodyScroll()
    await nextTick()
    // Focus the modal container
    if (modalRef.value) {
      modalRef.value.focus()
    }
    // Add tab key listener for focus trap
    document.addEventListener('keydown', handleTabKeyWrapper)
  } else {
    unlockBodyScroll()
    document.removeEventListener('keydown', handleTabKeyWrapper)
    // Return focus to previous element
    if (previousActiveElement.value) {
      previousActiveElement.value.focus()
    }
  }
})

function handleTabKeyWrapper(e) {
  if (e.key === 'Tab') {
    handleTabKey(e)
  }
}

function handleOverlayClick() {
  if (props.closeOnOverlay) {
    emit('close')
  }
}

function handleClose() {
  emit('close')
}

onUnmounted(() => {
  unlockBodyScroll()
  document.removeEventListener('keydown', handleTabKeyWrapper)
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal-container {
  background: #1a1a2e;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  max-height: calc(100vh - 32px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-sm {
  width: 100%;
  max-width: 320px;
}

.modal-md {
  width: 100%;
  max-width: 480px;
}

.modal-lg {
  width: 100%;
  max-width: 640px;
}

.modal-xl {
  width: 100%;
  max-width: 800px;
}

.modal-full {
  width: 100%;
  max-width: calc(100vw - 32px);
  max-height: calc(100vh - 32px);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.2s;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.modal-close:focus-visible {
  outline: 2px solid #667eea;
  outline-offset: 2px;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-active .modal-container,
.modal-fade-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .modal-container,
.modal-fade-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
