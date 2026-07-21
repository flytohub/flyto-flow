<template>
  <label class="param-checkbox">
    <input
      type="checkbox"
      :checked="modelValue"
      :disabled="readonly"
      @change="$emit('update:modelValue', $event.target.checked)"
    />
    <span class="checkbox-indicator"></span>
    <span v-if="label" class="checkbox-label">{{ label }}</span>
  </label>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  label: { type: String, default: '' },
  readonly: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.param-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.param-checkbox input {
  display: none;
}

.checkbox-indicator {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(71, 85, 105, 0.6);
  border-radius: 4px;
  background: rgba(15, 23, 42, 0.5);
  position: relative;
  transition: all 0.15s ease;
}

.param-checkbox input:checked + .checkbox-indicator {
  background: #8b5cf6;
  border-color: #8b5cf6;
}

.param-checkbox input:checked + .checkbox-indicator::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 1px;
  width: 4px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-label {
  font-size: 12px;
  color: #e2e8f0;
}
</style>
