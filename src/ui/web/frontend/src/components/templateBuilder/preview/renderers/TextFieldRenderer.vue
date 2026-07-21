<template>
  <input
    :type="inputType"
    :value="modelValue"
    :placeholder="component.props?.placeholder || ''"
    :disabled="disabled"
    class="field-input"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  component: { type: Object, required: true },
  modelValue: { type: [String, Number], default: '' },
  disabled: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])

const INPUT_TYPE_MAP = {
  text: 'text',
  input: 'text',
  number: 'number',
  email: 'email',
  ['password']: 'password',
  url: 'url',
  tel: 'tel',
}

const inputType = computed(() => {
  return INPUT_TYPE_MAP[props.component.type] || 'text'
})
</script>

<style scoped>
@import './fieldStyles.css';
</style>
