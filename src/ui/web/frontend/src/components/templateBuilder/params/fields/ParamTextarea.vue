<template>
  <textarea
    :value="modelValue"
    :placeholder="placeholder"
    :readonly="readonly"
    :rows="rows"
    class="param-textarea"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  readonly: { type: Boolean, default: false },
  rows: { type: Number, default: 3 },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.param-textarea {
  width: 100%;
  padding: 8px 10px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 6px;
  color: #e2e8f0;
  font-size: 12px;
  resize: vertical;
  min-height: 60px;
  transition: border-color 0.15s ease;
}

.param-textarea:focus {
  outline: none;
  border-color: rgba(139, 92, 246, 0.5);
}

.param-textarea:read-only {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
