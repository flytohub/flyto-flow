<template>
  <Teleport to="body">
    <Transition name="toast-slide">
      <div v-if="show" class="toast-container" :class="type">
        <div class="toast-icon">
          <component :is="iconComponent" :size="18" />
        </div>
        <span class="toast-message">{{ message }}</span>
        <button @click="copyMessage" class="toast-copy" aria-label="Copy message">
          <Check v-if="copied" :size="14" />
          <Copy v-else :size="14" />
        </button>
        <button @click="$emit('close')" class="toast-close" aria-label="Close">
          <X :size="16" />
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, ref } from 'vue'
import { CheckCircle, XCircle, AlertTriangle, Info, X, Copy, Check } from 'lucide-vue-next'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    default: 'success',
    validator: (value) => ['success', 'error', 'warning', 'info'].includes(value)
  },
  message: {
    type: String,
    default: ''
  }
})

defineEmits(['close'])

const copied = ref(false)

async function copyMessage() {
  try {
    await navigator.clipboard.writeText(props.message)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch { /* ignore */ }
}

const iconComponent = computed(() => {
  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info
  }
  return icons[props.type] || CheckCircle
})
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  background: #1e293b;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
  z-index: 1200;
  min-width: 280px;
  max-width: 500px;
  border: 1px solid rgba(71, 85, 105, 0.3);
}

.toast-container.success {
  border-color: rgba(16, 185, 129, 0.4);
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, #1e293b 100%);
}

.toast-container.error {
  border-color: rgba(239, 68, 68, 0.4);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, #1e293b 100%);
}

.toast-container.warning {
  border-color: rgba(245, 158, 11, 0.4);
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, #1e293b 100%);
}

.toast-container.info {
  border-color: rgba(59, 130, 246, 0.4);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, #1e293b 100%);
}

.toast-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.toast-container.success .toast-icon {
  color: #10b981;
}

.toast-container.error .toast-icon {
  color: #ef4444;
}

.toast-container.warning .toast-icon {
  color: #f59e0b;
}

.toast-container.info .toast-icon {
  color: #3b82f6;
}

.toast-message {
  flex: 1;
  font-size: 14px;
  color: #e2e8f0;
  line-height: 1.4;
}

.toast-copy {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.toast-copy:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #94a3b8;
}

.toast-close {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.toast-close:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #94a3b8;
}

/* Transition */
.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: all 0.3s ease;
}

.toast-slide-enter-from {
  opacity: 0;
  transform: translate(-50%, 20px);
}

.toast-slide-leave-to {
  opacity: 0;
  transform: translate(-50%, 20px);
}
</style>
