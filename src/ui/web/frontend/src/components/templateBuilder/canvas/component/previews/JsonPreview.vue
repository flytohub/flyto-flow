<template>
  <div class="json-preview">
    <PreviewLabel
      v-if="!hideLabel"
      :label="component.label"
      :required="component.validation?.required"
    />
    <textarea
      ref="inputRef"
      :value="localValue"
      :placeholder="component.placeholder || '{\n  \n}'"
      :disabled="!editable"
      :rows="component.rows || 4"
      class="preview-textarea"
      @input="handleInput"
      @focus="handleFocus"
      @blur="handleBlur"
    ></textarea>
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

function focus() {
  inputRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.json-preview {
  width: 100%;
}

.preview-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #475569;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.8);
  color: #f1f5f9;
  font-family: 'SF Mono', Monaco, Consolas, monospace;
  font-size: 12px;
  line-height: 1.5;
  resize: vertical;
  min-height: 60px;
  outline: none;
  transition: all 0.2s;
  box-sizing: border-box;
}

.preview-textarea::placeholder {
  color: #64748b;
}

.preview-textarea:focus {
  border-color: #8B5CF6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
}

.preview-textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
