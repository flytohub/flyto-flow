<template>
  <div class="path-preview">
    <PreviewLabel
      v-if="!hideLabel"
      :label="component.label"
      :required="component.validation?.required"
    />
    <div class="path-input-wrapper">
      <input
        ref="inputRef"
        type="text"
        :value="localValue"
        :placeholder="component.placeholder || '/path/to/file'"
        :disabled="!editable"
        class="preview-input"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
      />
      <button
        v-if="editable"
        type="button"
        class="browse-btn"
        :disabled="!editable"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"/>
        </svg>
      </button>
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

function focus() {
  inputRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.path-preview {
  width: 100%;
}

.path-input-wrapper {
  display: flex;
  align-items: center;
  gap: 0;
  border: 1px solid #475569;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.8);
  transition: all 0.2s;
}

.path-input-wrapper:focus-within {
  border-color: #8B5CF6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
}

.preview-input {
  flex: 1;
  min-width: 0;
  padding: 8px 12px;
  background: transparent;
  border: none;
  color: #f1f5f9;
  font-size: 13px;
  outline: none;
}

.preview-input::placeholder {
  color: #64748b;
}

.preview-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.browse-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  margin-right: 2px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.browse-btn:hover {
  background: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
}

.browse-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
