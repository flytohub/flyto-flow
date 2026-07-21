<template>
  <div class="range-preview">
    <PreviewLabel
      v-if="!hideLabel"
      :label="component.label"
      :required="component.validation?.required"
    />
    <div class="range-container">
      <input
        ref="inputRef"
        type="range"
        :value="localValue"
        :disabled="!editable"
        :min="component.min || 0"
        :max="component.max || 100"
        :step="component.step || 1"
        class="preview-range"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
      />
      <span class="range-value">{{ localValue }}</span>
    </div>
    <div v-if="showMinMax" class="range-labels">
      <span class="range-min">{{ component.min || 0 }}</span>
      <span class="range-max">{{ component.max || 100 }}</span>
    </div>
    <PreviewHelp :text="component.helpText" />
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import PreviewLabel from '@/components/common/PreviewLabel.vue'
import PreviewHelp from '@/components/common/PreviewHelp.vue'

const props = defineProps({
  component: {
    type: Object,
    required: true
  },
  editable: {
    type: Boolean,
    default: true
  },
  hideLabel: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update', 'focus', 'blur'])

const inputRef = ref(null)
const localValue = ref(props.component.default || props.component.min || 0)
const isFocused = ref(false)

const showMinMax = computed(() => props.component.showMinMax !== false)

watch(() => props.component.default, (newVal) => {
  if (!isFocused.value) {
    localValue.value = newVal ?? props.component.min ?? 0
  }
})

function handleInput(e) {
  const value = Number(e.target.value)
  localValue.value = value
  emit('update', { field: 'default', value })
}

function handleFocus() {
  isFocused.value = true
  emit('focus')
}

function handleBlur() {
  isFocused.value = false
  emit('blur')
}

function focus() {
  inputRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.range-preview {
  width: 100%;
}

.range-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.preview-range {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: #475569;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.preview-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: #8B5CF6;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.2s;
}

.preview-range::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.preview-range::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: #8B5CF6;
  border: none;
  border-radius: 50%;
  cursor: pointer;
}

.preview-range:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.preview-range:disabled::-webkit-slider-thumb {
  cursor: not-allowed;
}

.range-value {
  min-width: 40px;
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  color: #8B5CF6;
  background: rgba(139, 92, 246, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
}

.range-min,
.range-max {
  font-size: 10px;
  color: #64748b;
}
</style>
