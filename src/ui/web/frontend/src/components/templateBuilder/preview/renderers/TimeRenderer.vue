<template>
  <input
    type="time"
    :value="modelValue"
    :disabled="disabled"
    class="field-input"
    @input="$emit('update:modelValue', $event.target.value)"
  />
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
</style>
