<template>
  <button
    @click="!readonly && $emit('toggle-dropdown')"
    class="linked-display"
    :class="{ readonly: readonly }"
    :aria-expanded="isOpen"
    :aria-label="displayText"
  >
    <component :is="sourceType === 'ui_input' ? FormInput : GitBranch" :size="14" class="linked-icon" aria-hidden="true" />
    <span class="linked-text">{{ displayText }}</span>
    <ChevronDown v-if="!readonly" :size="12" class="linked-arrow" :class="{ rotated: isOpen }" aria-hidden="true" />
  </button>

  <!-- Linked Field Dropdown -->
  <Transition name="dropdown">
    <div v-if="isOpen" class="linked-dropdown custom-scrollbar">
      <template v-if="sourceType === 'ui_input'">
        <div v-if="uiInputFields.length === 0" class="no-fields">
          <Info :size="16" aria-hidden="true" />
          <span>{{ t('valueSource.noUIFields') }}</span>
        </div>
        <template v-for="field in uiInputFields" :key="field.variableName">
          <!-- Select type: show value + label options -->
          <template v-if="field.type === 'form.input_select' || field.type === 'form.select' || field.type === 'select'">
            <button
              @click="$emit('select-ui-input', field)"
              class="linked-option"
              :class="{ active: selectedUIInput === field.variableName }"
            >
              <component :is="getFieldIcon(field.type)" :size="14" class="field-icon" aria-hidden="true" />
              <div class="field-info">
                <span class="field-label">{{ field.label || field.variableName }}</span>
                <span class="field-var" aria-hidden="true">${{ field.variableName }}</span>
              </div>
              <span class="field-mode-tag">{{ t('valueSource.selectValue') }}</span>
            </button>
            <button
              @click="$emit('select-ui-input', { ...field, variableName: field.variableName + '__label', _labelMode: true })"
              class="linked-option"
              :class="{ active: selectedUIInput === field.variableName + '__label' }"
            >
              <Type :size="14" class="field-icon" aria-hidden="true" />
              <div class="field-info">
                <span class="field-label">{{ field.label || field.variableName }}</span>
                <span class="field-var" aria-hidden="true">${{ field.variableName }}__label</span>
              </div>
              <span class="field-mode-tag">{{ t('valueSource.selectText') }}</span>
            </button>
          </template>
          <!-- Other types: single entry -->
          <button
            v-else
            @click="$emit('select-ui-input', field)"
            class="linked-option"
            :class="{ active: selectedUIInput === field.variableName }"
          >
            <component :is="getFieldIcon(field.type)" :size="14" class="field-icon" aria-hidden="true" />
            <div class="field-info">
              <span class="field-label">{{ field.label || field.variableName }}</span>
              <span class="field-var" aria-hidden="true">${{ field.variableName }}</span>
            </div>
          </button>
        </template>
      </template>
      <template v-else>
        <div v-if="previousSteps.length === 0" class="no-fields">
          <Info :size="16" aria-hidden="true" />
          <span>{{ t('valueSource.noPreviousSteps') }}</span>
        </div>
        <button
          v-for="step in previousSteps"
          :key="step.id"
          @click="$emit('select-previous-step', step)"
          class="linked-option"
          :class="{ active: step.module === '__loop_context__'
            ? selectedStep === step.id
            : selectedStep === `steps.${step.id}.result` }"
        >
          <component
            :is="step.module === '__loop_context__' ? Repeat : getModuleIcon(step.module)"
            :size="14" class="field-icon" aria-hidden="true"
          />
          <div class="field-info">
            <span class="field-label">{{
              step.module === '__loop_context__'
                ? step.label
                : (resolveModuleLabel(step.module, modulesStore) || step.id)
            }}</span>
            <span class="field-var" aria-hidden="true">{{
              step.module === '__loop_context__'
                ? step.expression
                : `\${steps.${step.id}.result}`
            }}</span>
          </div>
        </button>
      </template>
    </div>
  </Transition>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { ChevronDown, Info, GitBranch, FormInput, Repeat, Type } from 'lucide-vue-next'
import { useModulesStore } from '@/stores/modulesStore'
import { resolveModuleLabel } from '@/utils/moduleIdUtils'

const { t } = useI18n()
const modulesStore = useModulesStore()

defineProps({
  sourceType: { type: String, required: true },
  readonly: { type: Boolean, default: false },
  isOpen: { type: Boolean, default: false },
  displayText: { type: String, default: '' },
  uiInputFields: { type: Array, default: () => [] },
  previousSteps: { type: Array, default: () => [] },
  selectedUIInput: { type: String, default: '' },
  selectedStep: { type: String, default: '' },
  getFieldIcon: { type: Function, required: true },
  getModuleIcon: { type: Function, required: true },
})

defineEmits(['toggle-dropdown', 'select-ui-input', 'select-previous-step'])
</script>

<style scoped>
.linked-display {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: transparent;
  border: none;
  color: #e2e8f0;
  font-size: 13px;
  cursor: pointer;
  text-align: left;
}

.linked-display:focus-visible {
  outline: 2px solid #8B5CF6;
  outline-offset: 2px;
}

.linked-display.readonly {
  cursor: default;
  opacity: 0.8;
}

.linked-icon {
  color: #8B5CF6;
  flex-shrink: 0;
}

.linked-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.linked-arrow {
  color: #64748b;
  flex-shrink: 0;
  transition: transform 0.2s;
}

.linked-arrow.rotated {
  transform: rotate(180deg);
}

.linked-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 40px;
  max-height: 220px;
  overflow-y: auto;
  background: linear-gradient(180deg, #0c1222 0%, #070b14 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 12px;
  padding: 6px;
  z-index: 100;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.5);
}

.no-fields {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: #64748b;
  font-size: 12px;
}

.linked-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  color: #cbd5e1;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
}

.linked-option:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.2);
}

.linked-option.active {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.4);
}

.field-icon {
  color: #8B5CF6;
}

.field-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.field-label {
  font-weight: 500;
}

.field-var {
  font-size: 10px;
  font-family: 'SF Mono', Monaco, monospace;
  color: #64748b;
}

.field-mode-tag {
  flex-shrink: 0;
  padding: 1px 6px;
  font-size: 10px;
  font-weight: 600;
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
  border-radius: 4px;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.4);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.4);
  border-radius: 3px;
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
