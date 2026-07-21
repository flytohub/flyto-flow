<template>
  <div class="empty-panel">
    <Inbox :size="48" class="empty-icon" />
    <p class="empty-title">{{ $t('templateBuilder.nodeProperties.noNodeSelected') }}</p>
    <p class="empty-desc">{{ $t('templateBuilder.nodeProperties.clickToEdit') }}</p>
  </div>
</template>

<script setup>
import { Inbox } from 'lucide-vue-next'
</script>

<style scoped>
.empty-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  color: #475569;
  margin-bottom: 16px;
}

.empty-title {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 600;
  color: #94a3b8;
}

.empty-desc {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}
</style>
