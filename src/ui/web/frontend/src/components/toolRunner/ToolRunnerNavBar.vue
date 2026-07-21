<template>
  <div class="nav-bar">
    <button class="back-btn" @click="$emit('back')">
      <ArrowLeft :size="20" />
      <span>{{ $t('toolRunner.backToLibrary') }}</span>
    </button>

    <div class="view-mode-tabs">
      <button
        class="tab-btn"
        :class="{ active: modelValue === 'simple' }"
        @click="$emit('update:modelValue', 'simple')"
      >
        <Zap :size="16" />
        {{ $t('toolRunner.simpleMode') }}
      </button>
      <button
        class="tab-btn"
        :class="{ active: modelValue === 'advanced' }"
        @click="$emit('update:modelValue', 'advanced')"
      >
        <Settings :size="16" />
        {{ $t('toolRunner.advancedMode') }}
      </button>
    </div>

    <button class="edit-btn" @click="$emit('edit')">
      <Edit3 :size="16" />
      {{ $t('toolRunner.editTool') }}
    </button>
  </div>
</template>

<script setup>
import { ArrowLeft, Zap, Settings, Edit3 } from 'lucide-vue-next'

defineProps({
  modelValue: {
    type: String,
    default: 'simple'
  }
})

defineEmits(['update:modelValue', 'back', 'edit'])
</script>

<style scoped>
.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: rgba(30, 41, 59, 0.9);
  border-bottom: 1px solid #334155;
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 100;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid #334155;
  border-radius: 8px;
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  border-color: #475569;
  color: #f1f5f9;
}

.view-mode-tabs {
  display: flex;
  background: #1e293b;
  border-radius: 8px;
  padding: 4px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #94a3b8;
}

.tab-btn.active {
  background: #334155;
  color: #f1f5f9;
}

.edit-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid #475569;
  border-radius: 8px;
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}
</style>
