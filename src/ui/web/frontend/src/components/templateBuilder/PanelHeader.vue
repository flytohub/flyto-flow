<template>
  <div class="panel-header">
    <div class="header-icon">
      <Settings :size="16" />
    </div>
    <h3 class="header-title">{{ title }}</h3>
  </div>
</template>

<script setup>
import { Settings } from 'lucide-vue-next'

defineProps({
  title: {
    type: String,
    required: true
  }
})
</script>

<style scoped>
.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  border-bottom: 1px solid #334155;
  background: rgba(30, 41, 59, 0.5);
}

.header-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.15) 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #A78BFA;
}

.header-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #f1f5f9;
}
</style>
