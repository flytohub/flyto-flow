<template>
  <div class="datetime-preview">
    <PreviewLabel
      v-if="!hideLabel"
      :label="component.label"
      :required="component.validation?.required"
    />
    <input
      ref="inputRef"
      type="datetime-local"
      :value="localValue"
      :disabled="!editable"
      :min="component.min"
      :max="component.max"
      class="preview-input"
      @input="handleInput"
      @focus="handleFocus"
      @blur="handleBlur"
    />
    <PreviewHelp :text="component.helpText" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PreviewLabel from '@/components/common/PreviewLabel.vue'
import PreviewHelp from '@/components/common/PreviewHelp.vue'
import { usePreviewInput } from '@/composables/usePreviewInput'

const props = defineProps({
  component: { type: Object, required: true },
  editable: { type: Boolean, default: true },
  hideLabel: { type: Boolean, default: false }
})

const emit = defineEmits(['update', 'focus', 'blur'])

const inputRef = ref(null)
const { localValue, handleFocus, handleBlur } = usePreviewInput(props, emit)

function handleInput(e) {
  emit('update', { field: 'default', value: e.target.value })
}

function focus() {
  inputRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.datetime-preview {
  width: 100%;
}

.preview-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #475569;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.8);
  color: #f1f5f9;
  font-size: 13px;
  transition: all 0.2s;
}

.preview-input::-webkit-calendar-picker-indicator {
  filter: invert(0.8);
  cursor: pointer;
}

.preview-input:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
}

.preview-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
