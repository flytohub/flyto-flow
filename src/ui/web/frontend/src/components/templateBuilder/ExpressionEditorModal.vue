<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="expression-modal-overlay"
        @click.self="cancel"
        @keydown.escape="cancel"
      >
        <div class="expression-modal" role="dialog" aria-modal="true" :aria-labelledby="titleId">
          <!-- Header -->
          <div class="modal-header">
            <h3 :id="titleId">{{ $t('expression.editExpression') }}</h3>
            <button
              @click="cancel"
              class="close-btn"
              :aria-label="$t('common.close')"
            >
              <X :size="20" aria-hidden="true" />
            </button>
          </div>

          <!-- Body: Split layout -->
          <div class="modal-body">
            <!-- Left: Editor Section -->
            <div class="editor-section">
              <div class="section-label">{{ $t('expression.expressionCode') }}</div>
              <ExpressionHighlighter
                ref="editorRef"
                v-model="localExpression"
                :placeholder="$t('expression.placeholder')"
                :suggestions="flattenedSuggestions"
              />
              <ExpressionPreview
                :expression="localExpression"
                :context="evaluationContext"
              />
            </div>

            <!-- Right: Variable Browser -->
            <div class="variable-section">
              <div class="section-label">{{ $t('expression.availableVariables') }}</div>
              <VariableSelector
                :available-variables="availableVariables"
                mode="inline"
                @select="insertVariable"
              />
            </div>
          </div>

          <!-- Footer -->
          <div class="modal-footer">
            <button @click="cancel" class="btn-secondary">
              {{ $t('common.cancel') }}
            </button>
            <button @click="apply" class="btn-primary">
              {{ $t('common.apply') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { X } from 'lucide-vue-next'
import ExpressionHighlighter from './shared/ExpressionHighlighter.vue'
import ExpressionPreview from './shared/ExpressionPreview.vue'
import VariableSelector from './shared/VariableSelector.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  initialValue: {
    type: String,
    default: ''
  },
  availableVariables: {
    type: Object,
    default: () => ({ inputs: [], steps: [], env: [] })
  },
  evaluationContext: {
    type: Object,
    default: () => ({ inputs: {}, steps: {}, env: {} })
  }
})

const emit = defineEmits(['save', 'cancel'])

const titleId = 'expression-editor-title'
const editorRef = ref(null)
const localExpression = ref('')

// Flatten available variables into autocomplete suggestions
const flattenedSuggestions = computed(() => {
  const suggestions = []
  const categoryColors = {
    inputs: '#22D3EE',  // cyan
    steps: '#A78BFA',   // purple
    env: '#4ADE80'      // green
  }

  // Process each category
  for (const category of ['inputs', 'steps', 'env']) {
    const items = props.availableVariables[category] || []
    for (const item of items) {
      suggestions.push({
        name: item.name || item.label || item.key,
        expression: item.expression || `\${${category}.${item.name || item.key}}`,
        category,
        color: categoryColors[category]
      })
    }
  }

  return suggestions
})

// Sync with initialValue when modal opens
watch(() => props.show, (isShowing) => {
  if (isShowing) {
    localExpression.value = props.initialValue || ''
    // Focus editor after mount
    nextTick(() => {
      editorRef.value?.focus()
    })
  }
})

// Also sync on initial value change while visible
watch(() => props.initialValue, (newVal) => {
  if (props.show) {
    localExpression.value = newVal || ''
  }
})

function insertVariable(variable) {
  if (!variable?.expression) return
  editorRef.value?.insertAtCursor(variable.expression)
}

function apply() {
  emit('save', localExpression.value)
}

function cancel() {
  emit('cancel')
}

// Handle escape key at document level
function handleKeydown(e) {
  if (e.key === 'Escape' && props.show) {
    cancel()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
/* Modal overlay */
.expression-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

/* Modal container */
.expression-modal {
  width: 90%;
  max-width: 900px;
  max-height: 80vh;
  background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5), 0 0 40px rgba(139, 92, 246, 0.1);
  overflow: hidden;
}

/* Header */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.4);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.close-btn:focus-visible {
  outline: 2px solid #8B5CF6;
  outline-offset: 2px;
}

/* Body - Split layout */
.modal-body {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  padding: 20px;
  overflow: hidden;
  flex: 1;
  min-height: 0;
}

/* Editor section */
.editor-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  overflow: hidden;
}

/* Variable browser section */
.variable-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  overflow: hidden;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
}

/* Footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid rgba(71, 85, 105, 0.4);
}

.btn-secondary {
  padding: 10px 20px;
  background: transparent;
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: rgba(71, 85, 105, 0.2);
  border-color: rgba(71, 85, 105, 0.7);
  color: #e2e8f0;
}

.btn-primary {
  padding: 10px 20px;
  background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #9D6FFF 0%, #8B5CF6 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary:focus-visible,
.btn-primary:focus-visible {
  outline: 2px solid #8B5CF6;
  outline-offset: 2px;
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .expression-modal,
.modal-leave-to .expression-modal {
  transform: scale(0.95) translateY(-10px);
  opacity: 0;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .modal-body {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr 1fr;
  }

  .expression-modal {
    max-height: 90vh;
    width: 95%;
  }
}
</style>
