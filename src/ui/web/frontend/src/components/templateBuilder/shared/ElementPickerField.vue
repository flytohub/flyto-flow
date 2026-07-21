<template>
  <div ref="containerRef" class="element-picker" :class="{ 'is-readonly': readonly }">
    <!-- Input + dropdown trigger -->
    <div class="picker-input-wrapper" :class="{ 'is-open': isOpen, 'has-source': sourceType !== 'static' }">

      <!-- Static mode: select-like trigger when hints have options -->
      <template v-if="sourceType === 'static' && isSelectMode">
        <button
          type="button"
          class="picker-select-trigger"
          :class="{ 'has-value': !!modelValue }"
          :disabled="readonly"
          @click.stop="toggle"
          @keydown.escape="close"
          @keydown.down.prevent="onArrowDown"
          @keydown.up.prevent="onArrowUp"
          @keydown.enter.prevent="onEnter"
        >
          <span class="select-display-text">{{ selectedDisplayLabel || placeholder }}</span>
          <ChevronDown :size="14" :class="{ 'rotate-180': isOpen }" />
        </button>
      </template>

      <!-- Static mode: text input (default element picker) -->
      <template v-else-if="sourceType === 'static'">
        <input
          ref="inputRef"
          type="text"
          class="picker-input"
          :value="modelValue"
          :placeholder="placeholder"
          :readonly="readonly"
          @input="onInput"
          @focus="onFocus"
          @keydown.escape="close"
          @keydown.down.prevent="onArrowDown"
          @keydown.up.prevent="onArrowUp"
          @keydown.enter.prevent="onEnter"
        />
        <!-- Element picker toggle -->
        <button
          v-if="!readonly"
          type="button"
          class="picker-toggle"
          :class="{ 'is-disabled': !hasSuggestions }"
          :disabled="!hasSuggestions"
          :title="toggleTitle"
          @click.stop="toggle"
        >
          <ChevronDown :size="14" :class="{ 'rotate-180': isOpen }" />
        </button>
      </template>

      <!-- Linked mode: UI Input / Previous Step -->
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

      <!-- Expression mode -->
      <ValueSourceExpression
        v-else-if="sourceType === 'expression'"
        v-model="localValue"
        :readonly="readonly"
        @input="emitValue"
        @open-editor="showExpressionEditor = true"
      />

      <!-- Settings (gear) icon — switch value source -->
      <button
        v-if="!readonly"
        type="button"
        class="settings-btn"
        :class="{ active: isSourceOpen, 'has-source': sourceType !== 'static' }"
        :title="t('valueSource.changeSource')"
        @click.stop="toggleSourceDropdown"
      >
        <Settings :size="14" />
      </button>
    </div>

    <!-- Source Type Dropdown -->
    <Transition name="dropdown">
      <div v-if="isSourceOpen" class="source-dropdown">
        <div class="dropdown-header">{{ t('valueSource.selectSourceType') }}</div>
        <button
          v-for="option in sourceOptions"
          :key="option.value"
          type="button"
          class="source-option"
          :class="{ active: sourceType === option.value }"
          @click="selectSource(option.value)"
        >
          <component :is="option.icon" :size="14" />
          <div class="option-info">
            <span class="option-label">{{ option.label }}</span>
            <span class="option-desc">{{ option.description }}</span>
          </div>
          <CheckCircle v-if="sourceType === option.value" :size="14" class="option-check" />
        </button>
      </div>
    </Transition>

    <!-- Element Picker / Select Dropdown (only in static mode) -->
    <ElementPickerDropdown
      v-if="sourceType === 'static'"
      :is-open="isOpen"
      :is-select-mode="isSelectMode"
      :filtered-suggestions="filteredSuggestions"
      :grouped-suggestions="groupedSuggestions"
      :focused-index="focusedIndex"
      :drop-direction="dropDirection"
      :is-item-selected="isItemSelected"
      @select-item="handleSelectItem"
      @update:focused-index="focusedIndex = $event"
    />

    <!-- Expression hint -->
    <div v-if="sourceType === 'expression'" class="expression-hint">
      <Info :size="12" />
      <span>{{ t('valueSource.expressionHint') }}</span>
    </div>

    <!-- Expression Editor Modal -->
    <ExpressionEditorModal
      :show="showExpressionEditor"
      :initial-value="fullExpressionValue"
      :available-variables="{ inputs: [], steps: [], env: [] }"
      :evaluation-context="{ inputs: {}, steps: {}, env: {} }"
      @save="handleExpressionSave"
      @cancel="showExpressionEditor = false"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ChevronDown, Settings, CheckCircle, Info } from 'lucide-vue-next'
import { useElementPicker } from '@/composables/useElementPicker'
import { useElementSuggestions } from '@/composables/useElementSuggestions'
import { useValueSource } from '@/composables/useValueSource'
import ValueSourceLinked from '@/components/valueSource/ValueSourceLinked.vue'
import ValueSourceExpression from '@/components/valueSource/ValueSourceExpression.vue'
import ExpressionEditorModal from '@/components/templateBuilder/ExpressionEditorModal.vue'
import ElementPickerDropdown from '@/components/templateBuilder/shared/ElementPickerDropdown.vue'

const { t } = useI18n()

const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '' },
  readonly: { type: Boolean, default: false },
  uiInputFields: { type: Array, default: () => [] },
  previousSteps: { type: Array, default: () => [] },
  allParams: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['update:value', 'update:modelValue', 'auto-switch-method'])

const {
  containerRef,
  dropdownRef,
  inputRef,
  isOpen,
  focusedIndex,
  dropDirection,
  toggle: pickerToggle,
  open: pickerOpen,
  close,
  updateDropDirection,
} = useElementPicker()

const showExpressionEditor = ref(false)

// --- Value Source (gear icon) ---
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
} = useValueSource(props, (event, val) => {
  if (event === 'update:modelValue') {
    emit('update:value', val)
    emit('update:modelValue', val)
  }
}, containerRef)

// --- Element Suggestions ---
const {
  suggestions,
  hasSuggestions,
  isSelectMode,
  selectedDisplayLabel,
  toggleTitle,
  filteredSuggestions,
  groupedSuggestions,
  totalFilteredCount,
  isItemSelected,
  selectItem,
} = useElementSuggestions(props, emit)

const fullExpressionValue = computed(() => {
  if (sourceType.value === 'expression' && localValue.value) {
    return `\${${localValue.value}}`
  }
  return ''
})

function handleExpressionSave(expression) {
  if (expression.startsWith('${') && expression.endsWith('}')) {
    localValue.value = expression.slice(2, -1)
  } else {
    localValue.value = expression
  }
  emitValue()
  showExpressionEditor.value = false
}

function handleSelectItem(item) {
  selectItem(item, close)
}

function onInput(e) {
  const val = e.target.value
  emit('update:value', val)
  emit('update:modelValue', val)
  if (hasSuggestions.value && !isOpen.value) {
    open()
  }
}

function onFocus() {
  if (hasSuggestions.value) {
    open()
  }
}

function toggle() {
  pickerToggle(hasSuggestions.value)
}

function open() {
  pickerOpen(hasSuggestions.value)
}

function onArrowDown() {
  if (!isOpen.value && hasSuggestions.value) {
    open()
    return
  }
  if (focusedIndex.value < totalFilteredCount.value - 1) {
    focusedIndex.value++
  }
}

function onArrowUp() {
  if (focusedIndex.value > 0) {
    focusedIndex.value--
  }
}

function onEnter() {
  if (focusedIndex.value >= 0 && focusedIndex.value < filteredSuggestions.value.length) {
    handleSelectItem(filteredSuggestions.value[focusedIndex.value])
  } else {
    close()
  }
}
</script>

<style scoped>
.element-picker {
  position: relative;
  width: 100%;
}

/* Always same layout: input + toggle button */
.picker-input-wrapper {
  display: flex;
  align-items: center;
  background: rgb(255 255 255 / 0.05);
  border: 1px solid rgb(71 85 105 / 0.5);
  border-radius: 8px;
  transition: all 0.15s;
}

.picker-input-wrapper:focus-within {
  border-color: rgb(139 92 246 / 0.6);
  box-shadow: 0 0 0 2px rgb(139 92 246 / 0.15);
}

.picker-input-wrapper.is-open {
  border-color: rgb(139 92 246 / 0.6);
}

.picker-input-wrapper.has-source {
  border-color: rgba(139, 92, 246, 0.3);
}

.picker-input {
  flex: 1;
  min-width: 0;
  padding: 8px 12px;
  background: transparent;
  border: none;
  outline: none;
  color: #e2e8f0;
  font-size: 13px;
  line-height: 1.5;
}

.picker-input::placeholder {
  color: rgb(100 116 139 / 0.7);
}

/* Select-like trigger (when hints populate options) */
.picker-select-trigger {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: transparent;
  border: none;
  color: #e2e8f0;
  font-size: 13px;
  line-height: 1.5;
  text-align: left;
  cursor: pointer;
}

.picker-select-trigger:not(.has-value) {
  color: rgb(100 116 139 / 0.7);
}

.picker-select-trigger:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.select-display-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker-select-trigger svg {
  flex-shrink: 0;
  margin-left: 8px;
  color: #64748b;
  transition: transform 0.2s;
}

/* Toggle button */
.picker-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}

.picker-toggle:hover:not(.is-disabled) {
  background: rgb(139 92 246 / 0.15);
  color: #a78bfa;
}

.picker-toggle.is-disabled {
  color: rgb(71 85 105 / 0.3);
  cursor: default;
}

.picker-toggle svg {
  transition: transform 0.2s;
}

.rotate-180 {
  transform: rotate(180deg);
}

/* Settings (gear) button */
.settings-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  margin-right: 4px;
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

/* Source Type Dropdown */
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

/* Expression hint */
.expression-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: 10px;
  color: #64748b;
}

/* Readonly */
.is-readonly .picker-input {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Transitions */
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
