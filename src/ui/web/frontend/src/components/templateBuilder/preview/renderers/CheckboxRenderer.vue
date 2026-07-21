<template>
  <label class="custom-control">
    <input
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      @change="$emit('update:modelValue', $event.target.checked)"
    />
    <span class="custom-control-indicator checkbox-indicator"></span>
    <span v-if="label" class="custom-control-label">{{ label }}</span>
  </label>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  component: { type: Object, required: true },
  modelValue: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])

const label = computed(() => {
  return props.component.props?.checkboxLabel || ''
})
</script>

<style scoped>
@import './fieldStyles.css';
</style>
