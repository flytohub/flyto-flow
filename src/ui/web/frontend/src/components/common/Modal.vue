<template>
  <BaseModal
    :show="modelValue"
    :title="title"
    :size="size"
    :show-header="showHeader"
    :show-close="showClose"
    :close-on-overlay="closeOnOverlay"
    @close="$emit('update:modelValue', false)"
  >
    <template v-if="$slots.header" #header>
      <slot name="header" />
    </template>
    <slot />
    <template v-if="$slots.footer" #footer>
      <slot name="footer" />
    </template>
  </BaseModal>
</template>

<script setup>
/**
 * Modal Component
 *
 * A v-model wrapper around BaseModal for convenience.
 * Use this when you want v-model binding for show/hide state.
 */
import BaseModal from './BaseModal.vue'

defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: ''
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg', 'xl', 'full'].includes(v)
  },
  showHeader: {
    type: Boolean,
    default: true
  },
  showClose: {
    type: Boolean,
    default: true
  },
  closeOnOverlay: {
    type: Boolean,
    default: true
  }
})

defineEmits(['update:modelValue'])
</script>
