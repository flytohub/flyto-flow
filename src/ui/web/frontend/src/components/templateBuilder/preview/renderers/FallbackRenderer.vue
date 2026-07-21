<template>
  <div class="fallback-field">
    <Package :size="14" />
    <span>{{ component.type }}: {{ fieldKey }}</span>
  </div>
</template>

<script setup>
import { Package } from 'lucide-vue-next'

defineProps({
  component: { type: Object, required: true },
  modelValue: { default: null },
  disabled: { type: Boolean, default: false },
  fieldKey: { type: String, default: '' },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
@import './fieldStyles.css';
</style>
