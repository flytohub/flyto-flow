<template>
  <div class="range-container">
    <input
      type="range"
      :value="modelValue"
      :min="minValue"
      :max="maxValue"
      :step="stepValue"
      :disabled="disabled"
      class="range-input"
      @input="$emit('update:modelValue', Number($event.target.value))"
    />
    <span class="range-value">{{ modelValue }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  component: { type: Object, required: true },
  modelValue: { type: Number, default: 0 },
  disabled: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])

const minValue = computed(() => props.component.props?.min ?? 0)
const maxValue = computed(() => props.component.props?.max ?? 100)
const stepValue = computed(() => props.component.props?.step ?? 1)
</script>

<style scoped>
@import './fieldStyles.css';
</style>
