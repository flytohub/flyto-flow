<template>
  <div class="radio-group">
    <label
      v-for="opt in options"
      :key="opt.value"
      class="custom-control"
    >
      <input
        type="radio"
        :name="fieldName"
        :value="opt.value"
        :checked="modelValue === opt.value"
        :disabled="disabled"
        @change="$emit('update:modelValue', opt.value)"
      />
      <span class="custom-control-indicator radio-indicator"></span>
      <span class="custom-control-label">{{ opt.label }}</span>
    </label>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  component: { type: Object, required: true },
  modelValue: { type: [String, Number], default: '' },
  disabled: { type: Boolean, default: false },
  fieldKey: { type: String, default: '' },
})

defineEmits(['update:modelValue'])

const options = computed(() => {
  return props.component.props?.options || []
})

const fieldName = computed(() => {
  return props.fieldKey || `radio-${Math.random().toString(36).slice(2)}`
})
</script>

<style scoped>
@import './fieldStyles.css';

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
