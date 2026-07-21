<template>
  <button
    :type="type"
    :class="[
      'loading-button',
      `variant-${variant}`,
      `size-${size}`,
      { 'is-loading': loading, 'is-disabled': disabled || loading }
    ]"
    :disabled="disabled || loading"
    :aria-busy="loading"
    @click="handleClick"
  >
    <Transition name="fade" mode="out-in">
      <span v-if="loading" class="loading-content">
        <Loader2 :size="iconSize" class="spinner" aria-hidden="true" />
        <span v-if="loadingText" class="loading-text">{{ loadingText }}</span>
      </span>
      <span v-else class="button-content">
        <component v-if="icon" :is="icon" :size="iconSize" class="button-icon" aria-hidden="true" />
        <slot />
      </span>
    </Transition>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { Loader2 } from 'lucide-vue-next'

const props = defineProps({
  type: {
    type: String,
    default: 'button'
  },
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'danger', 'ghost', 'outline'].includes(v)
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  loadingText: {
    type: String,
    default: ''
  },
  icon: {
    type: [Object, Function],
    default: null
  }
})

const emit = defineEmits(['click'])

const iconSize = computed(() => {
  const sizes = { sm: 14, md: 16, lg: 18 }
  return sizes[props.size]
})

function handleClick(event) {
  if (!props.loading && !props.disabled) {
    emit('click', event)
  }
}
</script>

<style scoped>
.loading-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 500;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

/* Sizes */
.size-sm {
  padding: 6px 12px;
  font-size: 13px;
  min-height: 44px;
}

.size-md {
  padding: 10px 20px;
  font-size: 14px;
  min-height: 44px;
}

.size-lg {
  padding: 14px 28px;
  font-size: 15px;
  min-height: 48px;
}

/* Variants */
.variant-primary {
  background: linear-gradient(135deg, #8b5cf6, #3b82f6);
  color: white;
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
}

.variant-primary:hover:not(.is-disabled) {
  box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4);
  transform: translateY(-1px);
}

.variant-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.variant-secondary:hover:not(.is-disabled) {
  background: #e5e7eb;
  border-color: #d1d5db;
}

:global(.dark) .variant-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-color: rgba(255, 255, 255, 0.2);
}

:global(.dark) .variant-secondary:hover:not(.is-disabled) {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.variant-danger {
  background: #fee2e2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.variant-danger:hover:not(.is-disabled) {
  background: #fecaca;
}

:global(.dark) .variant-danger {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border-color: rgba(239, 68, 68, 0.3);
}

:global(.dark) .variant-danger:hover:not(.is-disabled) {
  background: rgba(239, 68, 68, 0.3);
}

.variant-ghost {
  background: transparent;
  color: #6b7280;
}

.variant-ghost:hover:not(.is-disabled) {
  background: #f3f4f6;
  color: #374151;
}

:global(.dark) .variant-ghost {
  color: rgba(255, 255, 255, 0.7);
}

:global(.dark) .variant-ghost:hover:not(.is-disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.variant-outline {
  background: transparent;
  color: #8b5cf6;
  border: 1px solid rgba(139, 92, 246, 0.5);
}

.variant-outline:hover:not(.is-disabled) {
  background: rgba(139, 92, 246, 0.1);
  border-color: #8b5cf6;
}

/* States */
.is-disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

.is-loading {
  cursor: wait;
}

/* Focus visible for keyboard navigation */
.loading-button:focus-visible {
  outline: 2px solid #8b5cf6;
  outline-offset: 2px;
}

/* Content */
.button-content,
.loading-content {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.button-icon {
  flex-shrink: 0;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
