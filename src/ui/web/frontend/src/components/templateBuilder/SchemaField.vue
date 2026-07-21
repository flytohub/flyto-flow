<template>
  <div class="schema-field" :class="{ 'field-readonly': readonly, 'field-jsonEditor-type': fieldType === 'jsonEditor' }">
    <component
      :is="fieldComponent"
      v-bind="fieldProps"
      @update:value="handleUpdate"
      @update:modelValue="handleUpdate"
      @auto-switch-method="$emit('auto-switch-method', $event)"
    />
  </div>
</template>

<script setup>
import { computed, h } from 'vue'
import { useI18n } from 'vue-i18n'
import ValueSourceSelector from '../ValueSourceSelector.vue'
import KeyValueEditor from './shared/KeyValueEditor.vue'
import NestedObjectEditor from './shared/NestedObjectEditor.vue'
import AuthConfigEditor from './shared/AuthConfigEditor.vue'
import ArrayFieldEditor from './shared/ArrayFieldEditor.vue'
import ElementPickerField from './shared/ElementPickerField.vue'
import AppSelect from '../common/AppSelect.vue'
import { FormFileUpload, FormImageUpload } from '@/components/form'

const { t } = useI18n()

const props = defineProps({
  field: {
    type: Object,
    required: true
  },
  value: {
    type: [String, Number, Boolean, Array, Object],
    default: ''
  },
  readonly: {
    type: Boolean,
    default: false
  },
  uiInputFields: {
    type: Array,
    default: () => []
  },
  previousSteps: {
    type: Array,
    default: () => []
  },
  allParams: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:value', 'auto-switch-method'])

// ============================================
// Field Type Detection
// ============================================

// Backend is single source of truth for componentType.
// See: services/normalizers/base.py → _detect_component_type()
function detectFieldType(field) {
  return field.componentType || 'text'
}

const fieldType = computed(() => detectFieldType(props.field))

// ============================================
// Inline Components (select, boolean, slider)
// ============================================

// Select uses AppSelect (imported above) — no inline component needed

const BooleanField = {
  name: 'BooleanField',
  props: ['value', 'readonly'],
  emits: ['update:value'],
  setup(boolProps, { emit: boolEmit }) {
    const { t: bt } = useI18n()
    return () => h('label', { class: 'toggle-wrapper' }, [
      h('input', {
        type: 'checkbox',
        checked: boolProps.value,
        disabled: boolProps.readonly,
        class: 'toggle-input',
        onChange: (e) => boolEmit('update:value', e.target.checked)
      }),
      h('span', { class: 'toggle-slider' }),
      h('span', { class: 'toggle-label' },
        boolProps.value ? bt('common.enabled') : bt('common.disabled')
      )
    ])
  }
}

const SliderField = {
  name: 'SliderField',
  props: ['field', 'value', 'readonly'],
  emits: ['update:value'],
  setup(sliderProps, { emit: sliderEmit }) {
    return () => h('div', { class: 'slider-wrapper' }, [
      h('input', {
        type: 'range',
        value: sliderProps.value,
        min: sliderProps.field.min,
        max: sliderProps.field.max,
        step: sliderProps.field.step,
        disabled: sliderProps.readonly,
        class: 'field-slider',
        onInput: (e) => sliderEmit('update:value', parseFloat(e.target.value))
      }),
      h('span', { class: 'slider-value' }, sliderProps.value)
    ])
  }
}

// ============================================
// Component & Props mapping
// ============================================

const SPECIAL_COMPONENTS = {
  elementPicker: ElementPickerField,
  select: AppSelect,
  multiselect: AppSelect,
  array: ArrayFieldEditor,
  fileUpload: FormFileUpload,
  imageUpload: FormImageUpload,
  authConfig: AuthConfigEditor,
  nestedObject: NestedObjectEditor,
  keyValue: KeyValueEditor,
  boolean: BooleanField,
  slider: SliderField
}

const fieldComponent = computed(() => {
  return SPECIAL_COMPONENTS[fieldType.value] || ValueSourceSelector
})

// Shared VSS (ValueSourceSelector) props builder
function vssProps(inputType, placeholderOverride) {
  return {
    modelValue: props.value,
    inputType,
    placeholder: placeholderOverride || placeholder.value,
    readonly: props.readonly,
    uiInputFields: props.uiInputFields,
    previousSteps: props.previousSteps
  }
}

const SPECIAL_PROPS_BUILDERS = {
  elementPicker: () => ({
    field: props.field,
    modelValue: props.value,
    placeholder: placeholder.value,
    readonly: props.readonly,
    uiInputFields: props.uiInputFields,
    previousSteps: props.previousSteps,
    allParams: props.allParams
  }),
  select: () => {
    const rawOpts = props.field.options?.length > 0
      ? props.field.options
      : (props.field.enum || [])
    const options = rawOpts.map(opt => {
      if (typeof opt !== 'object') return { value: opt, label: String(opt) }
      const label = opt.label || opt.value
      return { value: opt.value, label }
    })
    return {
      modelValue: props.value,
      options,
      placeholder: placeholder.value,
      disabled: props.readonly
    }
  },
  array: () => ({
    field: props.field,
    value: Array.isArray(props.value) ? props.value : [],
    readOnly: props.readonly,
    placeholder: placeholder.value,
    uiInputFields: props.uiInputFields,
    previousSteps: props.previousSteps
  }),
  authConfig: () => ({
    modelValue: objectValue.value,
    readOnly: props.readonly,
    uiInputFields: props.uiInputFields,
    previousSteps: props.previousSteps
  }),
  nestedObject: () => ({
    field: props.field,
    modelValue: objectValue.value,
    readOnly: props.readonly,
    uiInputFields: props.uiInputFields,
    previousSteps: props.previousSteps
  }),
  keyValue: () => ({
    modelValue: objectValue.value,
    readOnly: props.readonly,
    keyLabel: t('common.key', 'Key'),
    valueLabel: t('common.value', 'Value'),
    addText: t('common.add', 'Add'),
    emptyText: t('common.noItems', 'No items'),
    uiInputFields: props.uiInputFields,
    previousSteps: props.previousSteps
  }),
  multiselect: () => {
    const rawOpts = props.field.options?.length > 0
      ? props.field.options
      : (props.field.enum || [])
    const options = rawOpts.map(opt => {
      if (typeof opt !== 'object') return { value: opt, label: String(opt) }
      return { value: opt.value, label: opt.label || opt.value }
    })
    return {
      modelValue: props.value,
      options,
      multiple: true,
      placeholder: placeholder.value,
      disabled: props.readonly
    }
  },
  fileUpload: () => ({
    modelValue: props.value,
    accept: props.field.accept || '*/*'
  }),
  imageUpload: () => ({
    modelValue: props.value,
    accept: props.field.accept || 'image/*'
  }),
  boolean: () => ({
    value: props.value,
    readonly: props.readonly
  }),
  slider: () => ({
    field: props.field,
    value: props.value,
    readonly: props.readonly
  }),
  path: () => vssProps('path', props.field.placeholder || '/path/to/file'),
  url: () => vssProps('url', props.field.placeholder || 'https://'),
  color: () => vssProps('color', props.field.placeholder || '#000000')
}

const fieldProps = computed(() => {
  const builder = SPECIAL_PROPS_BUILDERS[fieldType.value]
  if (builder) return builder()
  // Default: all other types (text, number, email, date, datetime, textarea, password, jsonEditor)
  return vssProps(fieldType.value === 'jsonEditor' ? 'textarea' : fieldType.value)
})

// ============================================
// Helpers
// ============================================

function handleUpdate(val) {
  if (fieldType.value === 'number') {
    emit('update:value', parseFloat(val) || 0)
  } else {
    emit('update:value', val)
  }
}

const objectValue = computed(() => {
  if (props.value && typeof props.value === 'object' && !Array.isArray(props.value)) {
    return props.value
  }
  return {}
})

const placeholder = computed(() => {
  return props.field.placeholder || t('common.enterValue', { field: props.field.label })
})
</script>

<style scoped>
.schema-field {
  width: 100%;
}

/* Boolean Toggle */
.toggle-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.toggle-input {
  display: none;
}

.toggle-slider {
  position: relative;
  width: 40px;
  height: 22px;
  background: rgba(71, 85, 105, 0.5);
  border-radius: 11px;
  transition: all 0.2s;
}

.toggle-slider::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  background: #94a3b8;
  border-radius: 50%;
  transition: all 0.2s;
}

.toggle-input:checked + .toggle-slider {
  background: rgba(139, 92, 246, 0.6);
}

.toggle-input:checked + .toggle-slider::after {
  left: 21px;
  background: #c4b5fd;
}

.toggle-label {
  font-size: 12px;
  color: #94a3b8;
}

.toggle-input:disabled + .toggle-slider {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Slider */
.slider-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.field-slider {
  flex: 1;
  height: 6px;
  background: rgba(71, 85, 105, 0.5);
  border-radius: 3px;
  appearance: none;
  cursor: pointer;
}

.field-slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  background: linear-gradient(135deg, #a78bfa 0%, #8B5CF6 100%);
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.15s;
}

.field-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.field-slider:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.slider-value {
  min-width: 40px;
  padding: 4px 8px;
  background: rgba(139, 92, 246, 0.15);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: #a78bfa;
  text-align: center;
}

/* Readonly state */
.field-readonly {
  opacity: 0.8;
}

/* JSON Editor monospace */
.field-jsonEditor-type :deep(.value-textarea) {
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 12px;
}
</style>
