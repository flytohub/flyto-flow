<template>
  <Teleport to="body">
    <TransitionGroup
      name="toast"
      tag="div"
      class="toast-container"
      role="region"
      :aria-label="t('accessibility.notifications')"
      aria-live="polite"
      aria-atomic="false"
    >
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="['toast', `toast-${toast.type}`]"
        role="alert"
        tabindex="0"
        :aria-label="`${toast.type}: ${toast.message}`"
        @click="dismiss(toast.id)"
        @keydown.enter="dismiss(toast.id)"
        @keydown.space.prevent="dismiss(toast.id)"
      >
        <component :is="getIcon(toast.type)" :size="18" class="toast-icon" aria-hidden="true" />
        <span class="toast-message">{{ toast.message }}</span>
        <button
          class="toast-copy"
          type="button"
          :aria-label="t('common.copy')"
          @click.stop="copyMessage(toast)"
        >
          <Check v-if="copiedId === toast.id" :size="14" aria-hidden="true" />
          <Copy v-else :size="14" aria-hidden="true" />
        </button>
        <button
          class="toast-close"
          type="button"
          :aria-label="t('common.dismiss')"
          @click.stop="dismiss(toast.id)"
        >
          <X :size="16" aria-hidden="true" />
        </button>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import { CheckCircle, XCircle, AlertTriangle, Info, X, Copy, Check } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { useToast } from '../../composables/useToast'

const { t } = useI18n()
const { toasts, dismiss } = useToast()
const copiedId = ref(null)

async function copyMessage(toast) {
  try {
    await navigator.clipboard.writeText(toast.message)
    copiedId.value = toast.id
    setTimeout(() => { copiedId.value = null }, 2000)
  } catch { /* ignore */ }
}

function getIcon(type) {
  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info
  }
  return icons[type] || Info
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 400px;
}

/* Mobile: center at bottom for better visibility */
@media (max-width: 640px) {
  .toast-container {
    top: auto;
    bottom: 20px;
    right: 16px;
    left: 16px;
    max-width: none;
  }
}

.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 10px;
  background: #1e293b;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  min-width: 280px;
}

.toast:focus-visible {
  outline: 2px solid #8b5cf6;
  outline-offset: 2px;
}

.toast-icon {
  flex-shrink: 0;
}

.toast-message {
  flex: 1;
  color: #e2e8f0;
  font-size: 14px;
  line-height: 1.4;
}

.toast-copy {
  flex-shrink: 0;
  padding: 6px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.toast-copy:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
}

.toast-close {
  flex-shrink: 0;
  min-width: 44px;
  min-height: 44px;
  padding: 10px;
  margin: -10px -10px -10px 0;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.toast-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
}

.toast-close:focus-visible {
  outline: 2px solid #8b5cf6;
  outline-offset: 2px;
}

.toast-success {
  border-left: 4px solid #22c55e;
}

.toast-success .toast-icon {
  color: #22c55e;
}

.toast-error {
  border-left: 4px solid #ef4444;
}

.toast-error .toast-icon {
  color: #ef4444;
}

.toast-warning {
  border-left: 4px solid #f59e0b;
}

.toast-warning .toast-icon {
  color: #f59e0b;
}

.toast-info {
  border-left: 4px solid #3b82f6;
}

.toast-info .toast-icon {
  color: #3b82f6;
}

/* Transitions */
.toast-enter-active {
  transition: all 0.3s ease-out;
}

.toast-leave-active {
  transition: all 0.2s ease-in;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>
