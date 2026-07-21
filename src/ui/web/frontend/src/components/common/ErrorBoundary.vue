<template>
  <div v-if="error" class="error-boundary">
    <div class="error-content">
      <div class="error-icon">
        <AlertTriangle :size="48" aria-hidden="true" />
      </div>
      <h2 class="error-title">{{ t('errors.somethingWentWrong') }}</h2>
      <p class="error-message">{{ errorMessage }}</p>
      <div class="error-actions">
        <button @click="retry" class="btn-primary">
          <RefreshCw :size="16" aria-hidden="true" />
          {{ t('common.retry') }}
        </button>
        <button @click="goHome" class="btn-secondary">
          <Home :size="16" aria-hidden="true" />
          {{ t('common.backToHome') }}
        </button>
      </div>
      <details v-if="showDetails && errorDetails" class="error-details">
        <summary>{{ t('errors.technicalDetails') }}</summary>
        <pre>{{ errorDetails }}</pre>
      </details>
    </div>
  </div>
  <slot v-else />
</template>

<script setup>
import { ref, onErrorCaptured, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { AlertTriangle, RefreshCw, Home } from 'lucide-vue-next'

const props = defineProps({
  showDetails: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['error', 'retry'])

const router = useRouter()
const { t } = useI18n()

const error = ref(null)
const errorInfo = ref(null)

const errorMessage = computed(() => {
  if (!error.value) return ''
  if (error.value.message) return error.value.message
  return t('errors.unexpectedError')
})

const errorDetails = computed(() => {
  if (!error.value) return ''
  return `${error.value.name}: ${error.value.message}\n${error.value.stack || ''}`
})

onErrorCaptured((err, instance, info) => {
  error.value = err
  errorInfo.value = info
  emit('error', { error: err, info })
  return false
})

function retry() {
  error.value = null
  errorInfo.value = null
  emit('retry')
}

function goHome() {
  error.value = null
  errorInfo.value = null
  router.push('/')
}

defineExpose({ reset: retry })
</script>

<style scoped>
.error-boundary {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.error-content {
  text-align: center;
  max-width: 480px;
}

.error-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 50%;
  color: #ef4444;
  margin-bottom: 1.5rem;
}

.error-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.dark .error-title {
  color: #f9fafb;
}

.error-message {
  color: #6b7280;
  margin-bottom: 1.5rem;
}

.dark .error-message {
  color: #9ca3af;
}

.error-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-primary,
.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  min-height: 44px;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 0.5rem;
  transition: all 0.2s;
  cursor: pointer;
  border: none;
}

.btn-primary:focus-visible,
.btn-secondary:focus-visible {
  outline: 2px solid #8b5cf6;
  outline-offset: 2px;
}

.btn-primary {
  background: linear-gradient(to right, #9333ea, #3b82f6);
  color: white;
}

.btn-primary:hover {
  box-shadow: 0 4px 12px rgba(147, 51, 234, 0.3);
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.dark .btn-secondary {
  background: #374151;
  color: #f9fafb;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.dark .btn-secondary:hover {
  background: #4b5563;
}

.error-details {
  margin-top: 1.5rem;
  text-align: left;
}

.error-details summary {
  cursor: pointer;
  color: #6b7280;
  font-size: 0.875rem;
}

.error-details pre {
  margin-top: 0.5rem;
  padding: 1rem;
  background: #f3f4f6;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.dark .error-details pre {
  background: #1f2937;
  color: #d1d5db;
}
</style>
