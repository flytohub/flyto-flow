<template>
  <div class="prop-group">
    <label class="prop-label">
      <FileText :size="14" />
      {{ $t('templateBuilder.nodeProperties.description') }}
    </label>
    <AppTextarea
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      :rows="2"
      :placeholder="$t('templateBuilder.nodeProperties.descriptionPlaceholder')"
      :readonly="readOnly"
      size="sm"
    />
  </div>
</template>

<script setup>
import { FileText } from 'lucide-vue-next'
import AppTextarea from '@/components/common/AppTextarea.vue'

defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  readOnly: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.prop-group {
  margin-bottom: 20px;
}

.prop-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 8px;
}

.prop-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #475569;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.6);
  color: #f1f5f9;
  font-size: 13px;
  resize: vertical;
  transition: all 0.2s;
}

.prop-textarea:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.prop-textarea[readonly] {
  cursor: default;
  opacity: 0.8;
}
</style>
