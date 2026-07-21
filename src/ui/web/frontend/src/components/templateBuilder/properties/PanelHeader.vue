<template>
  <div class="panel-header">
    <h3 class="header-title">
      <Settings :size="18" class="text-primary-600" />
      {{ $t('templateBuilder.properties.title') }}
    </h3>
    <button
      class="close-btn"
      :title="$t('common.close')"
      @click="$emit('close')"
    >
      <X :size="18" />
    </button>
  </div>
</template>

<script setup>
import { Settings, X } from 'lucide-vue-next'

defineEmits(['close'])
</script>

<style scoped>
.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #334155;
  background: rgba(30, 41, 59, 0.8);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.header-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #f1f5f9;
  display: flex;
  align-items: center;
  gap: 8px;
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: none;
  background: rgba(71, 85, 105, 0.3);
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}
</style>
