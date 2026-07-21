<template>
  <select
    :value="modelValue"
    :disabled="disabled"
    class="field-select"
    @change="$emit('update:modelValue', $event.target.value)"
  >
    <option value="" disabled>{{ placeholder }}</option>
    <option
      v-for="opt in options"
      :key="opt.value"
      :value="opt.value"
    >
      {{ opt.label }}
    </option>
  </select>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  component: { type: Object, required: true },
  modelValue: { type: [String, Number], default: '' },
  disabled: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])

const { t } = useI18n()

const placeholder = computed(() => {
  return props.component.props?.placeholder || `${t('common.select')}...`
})

const options = computed(() => {
  return props.component.props?.options || []
})
</script>

<style scoped>
@import './fieldStyles.css';
</style>
