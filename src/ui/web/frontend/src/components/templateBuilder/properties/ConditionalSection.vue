<template>
  <PropertyField
    :label="$t('templateBuilder.properties.conditionalDisplay')"
    :icon="Eye"
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :placeholder="$t('templateBuilder.properties.conditionalDisplayPlaceholder')"
    monospace
    expandable
    :settings-title="$t('templateBuilder.properties.moreOptions')"
  >
    <template #expanded>
      <small class="option-hint">{{ $t('templateBuilder.properties.conditionalDisplayHint') }}</small>
      <div class="option-examples">
        <code>field_id === 'value'</code>
        <code>checkbox_id === true</code>
        <code>number_id > 10</code>
      </div>
    </template>
  </PropertyField>
</template>

<script setup>
import { Eye } from 'lucide-vue-next'
import PropertyField from '../PropertyField.vue'

defineProps({
  modelValue: { type: String, default: '' }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.option-hint {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-bottom: 8px;
}

.option-examples {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option-examples code {
  padding: 4px 8px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 4px;
  font-size: 11px;
  font-family: 'SF Mono', Monaco, monospace;
  color: #a78bfa;
}
</style>
