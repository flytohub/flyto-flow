<template>
  <div class="delete-section">
    <button @click="$emit('delete')" class="delete-node-btn">
      <Trash2 :size="16" />
      {{ $t('templateBuilder.nodeProperties.deleteNode') }}
    </button>
  </div>
</template>

<script setup>
import { Trash2 } from 'lucide-vue-next'

defineEmits(['delete'])
</script>

<style scoped>
.delete-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #334155;
}

.delete-node-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.delete-node-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.5);
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.15);
}
</style>
