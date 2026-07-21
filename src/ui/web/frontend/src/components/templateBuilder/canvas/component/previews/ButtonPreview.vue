<template>
  <div class="button-preview">
    <button
      ref="buttonRef"
      :type="component.buttonType || 'button'"
      :disabled="!editable"
      :class="['preview-button', `variant-${component.variant || 'primary'}`]"
      @click="handleClick"
    >
      {{ component.text || 'Button' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

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

const emit = defineEmits(['update', 'focus', 'blur', 'click'])

const buttonRef = ref(null)

function handleClick(e) {
  e.preventDefault()
  emit('click')
}

function focus() {
  buttonRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.button-preview {
  width: 100%;
}

.preview-button {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.preview-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.preview-button.variant-primary {
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  color: white;
}

.preview-button.variant-primary:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.preview-button.variant-secondary {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
  border: 1px solid #475569;
}

.preview-button.variant-secondary:hover:not(:disabled) {
  background: rgba(71, 85, 105, 0.7);
}

.preview-button.variant-danger {
  background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
  color: white;
}

.preview-button.variant-danger:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}
</style>
