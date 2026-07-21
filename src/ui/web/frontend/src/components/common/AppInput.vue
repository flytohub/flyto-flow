<template>
  <input
    ref="inputRef"
    :value="modelValue"
    :type="type"
    :placeholder="placeholder"
    :disabled="disabled"
    :readonly="readonly"
    :class="inputClasses"
    @input="$emit('update:modelValue', $event.target.value)"
    @blur="$emit('blur', $event)"
    @focus="$emit('focus', $event)"
    @keydown="$emit('keydown', $event)"
  />
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  placeholder: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  readonly: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'md',
    validator: v => ['sm', 'md'].includes(v)
  }
})

defineEmits(['update:modelValue', 'blur', 'focus', 'keydown'])

const inputRef = ref(null)

const inputClasses = computed(() => {
  const base = 'w-full bg-white dark:bg-gray-800 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20'
  const border = 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
  const sizing = props.size === 'sm'
    ? 'px-3 py-1.5 text-sm min-h-[34px]'
    : 'px-4 py-2.5 text-sm min-h-[42px]'
  const state = props.disabled
    ? 'opacity-50 cursor-not-allowed'
    : props.readonly
      ? 'opacity-70 cursor-default'
      : ''
  return [base, border, sizing, state]
})

defineExpose({
  inputRef,
  focus: () => inputRef.value?.focus(),
  blur: () => inputRef.value?.blur(),
})
</script>
