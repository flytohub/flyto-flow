<template>
  <select
    :value="modelValue"
    :disabled="readonly"
    class="param-select"
    @change="$emit('update:modelValue', $event.target.value)"
  >
    <option value="" disabled>{{ placeholder }}</option>
    <option
      v-for="opt in normalizedOptions"
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
  modelValue: { type: [String, Number], default: '' },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: '' },
  readonly: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])

const { t } = useI18n()

const normalizedOptions = computed(() => {
  return props.options.map(opt => {
    if (typeof opt === 'string') {
      return { value: opt, label: opt }
    }
    return opt
  })
})
</script>

<style scoped>
.param-select {
  width: 100%;
  padding: 8px 10px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 6px;
  color: #e2e8f0;
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.15s ease;
}

.param-select:focus {
  outline: none;
  border-color: rgba(139, 92, 246, 0.5);
}

.param-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
