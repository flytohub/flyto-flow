<template>
  <input
    :value="modelValue"
    :placeholder="placeholder"
    :readonly="readonly"
    type="text"
    class="param-input"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>

<script setup>
defineProps({
  modelValue: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '' },
  readonly: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.param-input {
  width: 100%;
  padding: 8px 10px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 6px;
  color: #e2e8f0;
  font-size: 12px;
  transition: border-color 0.15s ease;
}

.param-input:focus {
  outline: none;
  border-color: rgba(139, 92, 246, 0.5);
}

.param-input:read-only {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
