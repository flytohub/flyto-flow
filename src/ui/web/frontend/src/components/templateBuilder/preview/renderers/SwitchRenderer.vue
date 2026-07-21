<template>
  <label class="switch-container">
    <input
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      class="switch-input"
      @change="$emit('update:modelValue', $event.target.checked)"
    />
    <span :class="['switch-track', { active: modelValue }]">
      <span class="switch-thumb"></span>
    </span>
  </label>
</template>

<script setup>
defineProps({
  component: { type: Object, required: true },
  modelValue: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
@import './fieldStyles.css';

.switch-container {
  display: inline-flex;
  cursor: pointer;
}

.switch-input {
  display: none;
}
</style>
