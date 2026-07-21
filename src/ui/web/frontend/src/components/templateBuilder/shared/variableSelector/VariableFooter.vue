<template>
  <div v-if="show" class="var-footer">
    <div class="selected-preview">
      <span class="preview-label">{{ $t('variableSelector.selected') }}:</span>
      <code class="preview-value">{{ expression }}</code>
    </div>
    <button class="insert-btn" @click="$emit('confirm')">
      <Plus :size="14" />
      {{ $t('variableSelector.insert') }}
    </button>
  </div>
</template>

<script setup>
import { Plus } from 'lucide-vue-next'

defineProps({
  show: { type: Boolean, default: false },
  expression: { type: String, default: '' }
})

defineEmits(['confirm'])
</script>

<style scoped>
.var-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.6);
  border-top: 1px solid rgba(71, 85, 105, 0.3);
}

.selected-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.preview-label {
  font-size: 11px;
  color: #64748b;
  flex-shrink: 0;
}

.preview-value {
  font-size: 11px;
  font-family: 'SF Mono', Monaco, monospace;
  color: #a78bfa;
  background: rgba(139, 92, 246, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.insert-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.insert-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}
</style>
