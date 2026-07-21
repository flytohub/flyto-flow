<template>
  <div class="value-source-selector" ref="selectorRef">
    <!-- Inline Input with Settings Icon -->
    <div class="input-wrapper">
      <!-- Static Value Input (default) -->
      <ValueSourceLiteral
        v-if="sourceType === 'static'"
        v-model="localValue"
        :input-type="inputType"
        :placeholder="placeholder"
        :readonly="readonly"
        @input="emitValue"
        @browse-path="browsePath"
      />

      <!-- Linked Value Display (UI Input / Previous Step) -->
      <ValueSourceLinked
        v-else-if="sourceType === 'ui_input' || sourceType === 'previous_step'"
        :source-type="sourceType"
        :readonly="readonly"
        :is-open="isLinkedOpen"
        :display-text="linkedDisplayText"
        :ui-input-fields="uiInputFields"
        :previous-steps="previousSteps"
        :selected-u-i-input="selectedUIInput"
        :selected-step="selectedStep"
        :get-field-icon="getFieldIcon"
        :get-module-icon="getModuleIcon"
        @toggle-dropdown="toggleLinkedDropdown"
        @select-ui-input="selectUIInput"
        @select-previous-step="selectPreviousStep"
      />

      <!-- Expression Input -->
      <ValueSourceExpression
        v-else-if="sourceType === 'expression'"
        v-model="localValue"
        :readonly="readonly"
        @input="emitValue"
        @open-editor="openExpressionEditor"
      />

      <!-- Settings Icon Button -->
      <button
        v-if="!readonly"
        @click="toggleSourceDropdown"
        class="settings-btn"
        :class="{ active: isSourceOpen, 'has-source': sourceType !== 'static' }"
        :aria-label="t('valueSource.changeSource')"
        :aria-expanded="isSourceOpen"
      >
        <Settings :size="14" aria-hidden="true" />
      </button>
    </div>

    <!-- Source Type Dropdown (appears when clicking settings icon) -->
    <Transition name="dropdown">
      <div v-if="isSourceOpen" class="source-dropdown">
        <div class="dropdown-header">{{ t('valueSource.selectSourceType') }}</div>
        <button
          v-for="option in sourceOptions"
          :key="option.value"
          @click="selectSource(option.value)"
          class="source-option"
          :class="{ active: sourceType === option.value }"
          :aria-pressed="sourceType === option.value"
        >
          <component :is="option.icon" :size="14" aria-hidden="true" />
          <div class="option-info">
            <span class="option-label">{{ option.label }}</span>
            <span class="option-desc">{{ option.description }}</span>
          </div>
          <CheckCircle v-if="sourceType === option.value" :size="14" class="option-check" aria-hidden="true" />
        </button>
      </div>
    </Transition>

    <!-- Expression Hint -->
    <div v-if="sourceType === 'expression'" class="expression-hint">
      <Info :size="12" aria-hidden="true" />
      <span>{{ t('valueSource.expressionHint') }}</span>
    </div>

    <!-- Expression Editor Modal -->
    <ExpressionEditorModal
      :show="showExpressionEditor"
      :initial-value="fullExpressionValue"
      :available-variables="availableVariables"
      :evaluation-context="evaluationContext"
      @save="handleExpressionSave"
      @cancel="showExpressionEditor = false"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CheckCircle, Info, Settings } from 'lucide-vue-next'
import { get } from '@/api/client'
import { useValueSource } from '@/composables/useValueSource'
import ExpressionEditorModal from '@/components/templateBuilder/ExpressionEditorModal.vue'
import ValueSourceLiteral from '@/components/valueSource/ValueSourceLiteral.vue'
import ValueSourceLinked from '@/components/valueSource/ValueSourceLinked.vue'
import ValueSourceExpression from '@/components/valueSource/ValueSourceExpression.vue'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean, Object],
    default: ''
  },
  inputType: {
    type: String,
    default: 'text'
  },
  placeholder: {
    type: String,
    default: ''
  },
  uiInputFields: {
    type: Array,
    default: () => []
  },
  previousSteps: {
    type: Array,
    default: () => []
  },
  paramKey: {
    type: String,
    default: ''
  },
  readonly: {
    type: Boolean,
    default: false
  },
  browseMode: {
    type: String,
    default: 'file'
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

const emit = defineEmits(['update:modelValue'])
const selectorRef = ref(null)
const showExpressionEditor = ref(false)

const {
  sourceType,
  localValue,
  selectedUIInput,
  selectedStep,
  isSourceOpen,
  isLinkedOpen,
  linkedDisplayText,
  sourceOptions,
  getFieldIcon,
  getModuleIcon,
  toggleSourceDropdown,
  toggleLinkedDropdown,
  selectSource,
  selectUIInput,
  selectPreviousStep,
  emitValue
} = useValueSource(props, emit, selectorRef)

const fullExpressionValue = computed(() => {
  if (sourceType.value === 'expression' && localValue.value) {
    return `\${${localValue.value}}`
  }
  return ''
})

function openExpressionEditor() {
  showExpressionEditor.value = true
}

function handleExpressionSave(expression) {
  if (expression.startsWith('${') && expression.endsWith('}')) {
    localValue.value = expression.slice(2, -1)
  } else {
    localValue.value = expression
  }
  emitValue()
  showExpressionEditor.value = false
}

async function browsePath() {
  try {
    const result = await get(`/utils/browse-path?mode=${props.browseMode}`)
    if (result.ok && result.path) {
      localValue.value = result.path
      emitValue()
    }
  } catch {
    // Not available in cloud mode
  }
}
</script>

<style scoped>
.value-source-selector {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(7, 11, 20, 0.9) 100%);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  box-sizing: border-box;
  transition: all 0.2s;
}

.input-wrapper:focus-within {
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.input-wrapper:has(.linked-display),
.input-wrapper:has(.expression-input) {
  border-color: rgba(139, 92, 246, 0.3);
}

.input-wrapper:has(.linked-display):hover {
  border-color: rgba(139, 92, 246, 0.5);
}

.settings-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.settings-btn:hover {
  background: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
}

.settings-btn.active {
  background: rgba(139, 92, 246, 0.2);
  color: #8B5CF6;
}

.settings-btn.has-source {
  color: #8B5CF6;
}

.settings-btn:focus-visible {
  outline: 2px solid #8B5CF6;
  outline-offset: 2px;
}

.source-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  width: 280px;
  background: linear-gradient(180deg, #0c1222 0%, #070b14 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 12px;
  padding: 6px;
  z-index: 100;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.5), 0 0 30px rgba(139, 92, 246, 0.1);
}

.dropdown-header {
  padding: 8px 12px;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.source-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
}

.source-option:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.2);
  color: #e2e8f0;
}

.source-option.active {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.4);
  color: #f1f5f9;
}

.option-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-label {
  font-weight: 600;
  color: inherit;
}

.option-desc {
  font-size: 10px;
  color: #64748b;
}

.option-check {
  color: #8B5CF6;
}

.expression-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: #64748b;
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
