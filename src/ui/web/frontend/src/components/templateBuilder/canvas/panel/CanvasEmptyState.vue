<template>
  <div class="canvas-empty">
    <Inbox :size="64" class="empty-icon" />
    <p class="empty-title">{{ $t('templateBuilder.canvas.emptyState') }}</p>
    <p class="empty-hint">{{ $t('templateBuilder.canvas.emptyStateDetail') }}</p>
  </div>
</template>

<script setup>
import { Inbox } from 'lucide-vue-next'
</script>

<style scoped>
.canvas-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.empty-icon {
  margin-bottom: 16px;
  color: #475569;
}

.empty-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 500;
  color: #64748b;
}

.empty-hint {
  margin: 0;
  font-size: 14px;
  color: #475569;
}
</style>
