<template>
  <textarea
    ref="textareaRef"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :readonly="readonly"
    :rows="rows"
    :class="textareaClasses"
    @input="onInput"
    @blur="$emit('blur', $event)"
    @focus="$emit('focus', $event)"
    @keydown="$emit('keydown', $event)"
  />
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
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
  rows: {
    type: Number,
    default: 4
  },
  maxRows: {
    type: Number,
    default: 0
  },
  autoResize: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'md',
    validator: v => ['sm', 'md'].includes(v)
  }
})

const emit = defineEmits(['update:modelValue', 'blur', 'focus', 'keydown'])

const textareaRef = ref(null)

const textareaClasses = computed(() => {
  const base = 'w-full bg-white dark:bg-gray-800 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 resize-vertical'
  const border = 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
  const sizing = props.size === 'sm'
    ? 'px-3 py-1.5 text-sm'
    : 'px-4 py-2.5 text-sm'
  const state = props.disabled
    ? 'opacity-50 cursor-not-allowed'
    : props.readonly
      ? 'opacity-70 cursor-default'
      : ''
  const resize = props.autoResize ? 'resize-none overflow-hidden' : ''
  return [base, border, sizing, state, resize]
})

function onInput(e) {
  emit('update:modelValue', e.target.value)
  if (props.autoResize) nextTick(adjustHeight)
}

function adjustHeight() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  let newHeight = el.scrollHeight
  if (props.maxRows > 0) {
    const lineHeight = parseFloat(getComputedStyle(el).lineHeight) || 20
    const maxHeight = lineHeight * props.maxRows
    newHeight = Math.min(newHeight, maxHeight)
  }
  el.style.height = newHeight + 'px'
}

if (props.autoResize) {
  onMounted(() => nextTick(adjustHeight))
  watch(() => props.modelValue, () => nextTick(adjustHeight))
}

defineExpose({ textareaRef })
</script>
