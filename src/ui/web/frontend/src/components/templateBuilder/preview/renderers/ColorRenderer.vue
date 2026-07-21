<template>
  <div class="color-field">
    <input
      type="color"
      :value="modelValue || '#000000'"
      :disabled="disabled"
      class="color-swatch"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <input
      type="text"
      :value="modelValue"
      :placeholder="component.props?.placeholder || '#000000'"
      :disabled="disabled"
      class="field-input color-text"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  </div>
</template>

<script setup>
defineProps({
  component: { type: Object, required: true },
  modelValue: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
@import './fieldStyles.css';

.color-field {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-swatch {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  padding: 2px;
  background: transparent;
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: var(--radius-md, 6px);
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

.color-text {
  flex: 1;
  min-width: 0;
}
</style>
