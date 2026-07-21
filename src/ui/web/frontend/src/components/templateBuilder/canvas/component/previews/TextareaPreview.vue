<template>
  <div class="textarea-preview">
    <PreviewLabel
      :label="component.label"
      :required="component.validation?.required"
    />
    <textarea
      ref="textareaRef"
      :value="localValue"
      :placeholder="component.placeholder || ''"
      :disabled="!editable"
      :readonly="component.readonly"
      :rows="component.rows || 3"
      class="preview-textarea"
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
  component: {
    type: Object,
    required: true
  },
  editable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update', 'focus', 'blur'])

const textareaRef = ref(null)
const { localValue, handleInput, handleFocus, handleBlur } = usePreviewInput(props, emit)

function focus() {
  textareaRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.textarea-preview {
  width: 100%;
}

.preview-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #475569;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.8);
  color: #f1f5f9;
  font-size: 13px;
  resize: vertical;
  min-height: 60px;
  transition: all 0.2s;
}

.preview-textarea::placeholder {
  color: #64748b;
}

.preview-textarea:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
}

.preview-textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.preview-textarea:read-only {
  background: rgba(30, 41, 59, 0.5);
}
</style>
