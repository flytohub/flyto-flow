<template>
  <NumberInput
    :modelValue="modelValue"
    :placeholder="placeholder"
    :readonly="readonly"
    :min="min"
    :max="max"
    :step="step"
    inputClass="param-input"
    @update:modelValue="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
import NumberInput from '@/components/common/NumberInput.vue'

defineProps({
  modelValue: { type: Number, default: 0 },
  placeholder: { type: String, default: '' },
  readonly: { type: Boolean, default: false },
  min: { type: Number, default: undefined },
  max: { type: Number, default: undefined },
  step: { type: Number, default: 1 },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
:deep(.param-input) {
  width: 100%;
  padding: 8px 10px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 6px;
  color: #e2e8f0;
  font-size: 12px;
  transition: border-color 0.15s ease;
}

:deep(.param-input:focus) {
  outline: none;
  border-color: rgba(139, 92, 246, 0.5);
}

:deep(.param-input:read-only) {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
