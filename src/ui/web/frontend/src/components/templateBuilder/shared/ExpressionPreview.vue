<template>
  <div class="expression-preview" :class="{ error: !isValid, empty: !expression }">
    <div class="preview-header">
      <Eye :size="14" aria-hidden="true" />
      <span>{{ $t('expression.preview') }}</span>
    </div>
    <div class="preview-content">
      <template v-if="!expression">
        <span class="empty-message">{{ $t('expression.enterExpression') }}</span>
      </template>
      <template v-else-if="isValid">
        <pre class="preview-value">{{ formattedValue }}</pre>
      </template>
      <template v-else>
        <AlertCircle :size="14" class="error-icon" aria-hidden="true" />
        <span class="error-message">{{ error }}</span>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Eye, AlertCircle } from 'lucide-vue-next'
import { ExpressionEvaluator } from '@/services/ExpressionEvaluator'

const props = defineProps({
  expression: {
    type: String,
    default: ''
  },
  context: {
    type: Object,
    default: () => ({ inputs: {}, steps: {}, env: {} })
  }
})

// Evaluate the expression
const evaluationResult = computed(() => {
  if (!props.expression) {
    return { ok: true, value: undefined }
  }

  const evaluator = new ExpressionEvaluator(props.context)
  return evaluator.evaluate(props.expression)
})

const isValid = computed(() => evaluationResult.value.ok)

const error = computed(() => {
  if (evaluationResult.value.ok) return ''
  return evaluationResult.value.error || 'Invalid expression'
})

const formattedValue = computed(() => {
  const value = evaluationResult.value.value

  if (value === undefined || value === null) {
    return 'null'
  }

  if (typeof value === 'object') {
    try {
      return JSON.stringify(value, null, 2)
    } catch {
      return String(value)
    }
  }

  if (typeof value === 'string') {
    return `"${value}"`
  }

  return String(value)
})
</script>

<style scoped>
.expression-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 8px;
  transition: all 0.2s;
}

.expression-preview.error {
  border-color: rgba(248, 113, 113, 0.4);
  background: rgba(127, 29, 29, 0.15);
}

.expression-preview.empty {
  opacity: 0.7;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
}

.preview-content {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  min-height: 24px;
}

.preview-value {
  margin: 0;
  padding: 0;
  font-family: 'SF Mono', Monaco, 'Fira Code', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #4ade80;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 100px;
  overflow-y: auto;
}

.empty-message {
  font-size: 12px;
  color: #64748b;
  font-style: italic;
}

.error-icon {
  flex-shrink: 0;
  color: #f87171;
  margin-top: 2px;
}

.error-message {
  font-size: 12px;
  color: #f87171;
  line-height: 1.4;
}

/* Scrollbar for preview value */
.preview-value::-webkit-scrollbar {
  width: 4px;
}

.preview-value::-webkit-scrollbar-track {
  background: transparent;
}

.preview-value::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.4);
  border-radius: 2px;
}
</style>
