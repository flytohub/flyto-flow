<template>
  <div class="column-empty">
    <Plus :size="28" />
    <p class="empty-title">{{ $t('templateBuilder.section.clickToSelect') }}</p>
    <p class="empty-hint">{{ $t('templateBuilder.section.addComponentsFromLeft') }}</p>
  </div>
</template>

<script setup>
import { Plus } from 'lucide-vue-next'
</script>

<style scoped>
.column-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 80px;
  color: #64748b;
  text-align: center;
}

.empty-title {
  margin: 8px 0 2px;
  font-size: 12px;
  font-weight: 500;
}

.empty-hint {
  margin: 0;
  font-size: 11px;
  color: #475569;
}
</style>
