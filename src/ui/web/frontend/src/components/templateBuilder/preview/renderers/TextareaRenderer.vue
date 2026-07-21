<template>
  <textarea
    :value="modelValue"
    :placeholder="component.props?.placeholder || ''"
    :rows="component.props?.rows || 4"
    :disabled="disabled"
    class="field-textarea"
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
