<template>
  <div class="color-preview">
    <PreviewLabel
      v-if="!hideLabel"
      :label="component.label"
      :required="component.validation?.required"
    />
    <div class="color-input-wrapper">
      <input
        type="color"
        :value="localValue || '#000000'"
        :disabled="!editable"
        class="color-swatch"
        @input="handleColorInput"
      />
      <input
        ref="inputRef"
        type="text"
        :value="localValue"
        placeholder="#000000"
        :disabled="!editable"
        class="preview-input color-text"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
      />
    </div>
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
const { localValue, handleInput, handleFocus, handleBlur } = usePreviewInput(props, emit)

function handleColorInput(e) {
  emit('update', { field: 'default', value: e.target.value })
}

function focus() {
  inputRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.color-preview {
  width: 100%;
}

.color-input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-swatch {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  padding: 2px;
  background: transparent;
  border: 1px solid #475569;
  border-radius: 6px;
  cursor: pointer;
}

.color-swatch::-webkit-color-swatch-wrapper {
  padding: 0;
}

.color-swatch::-webkit-color-swatch {
  border: none;
  border-radius: 4px;
}

.color-swatch:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.preview-input {
  flex: 1;
  min-width: 0;
  padding: 8px 12px;
  border: 1px solid #475569;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.8);
  color: #f1f5f9;
  font-size: 13px;
  transition: all 0.2s;
}

.preview-input::placeholder {
  color: #64748b;
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
