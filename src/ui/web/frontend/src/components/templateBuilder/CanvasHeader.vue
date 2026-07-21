<template>
  <div class="canvas-header">
    <div class="header-left">
      <div class="header-icon preview-icon">
        <Eye :size="16" />
      </div>
      <span class="header-title">{{ $t('templateBuilder.canvas.livePreview') }}</span>
    </div>

    <div class="header-actions">
      <div class="relative">
        <button
          @click="$emit('toggle-layout-picker')"
          class="action-btn primary"
        >
          <Plus :size="16" />
          {{ $t('templateBuilder.canvas.addSection') }}
        </button>

        <LayoutPickerDropdown
          v-if="showLayoutPicker"
          @select="$emit('add-section', $event)"
        />
      </div>

      <button
        v-if="hasSelectedComponent"
        @click="$emit('toggle-properties')"
        class="action-btn secondary"
      >
        <Settings :size="16" />
        {{ showPropertiesPanel
          ? $t('templateBuilder.canvas.closeProperties')
          : $t('templateBuilder.canvas.componentProperties') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { Eye, Plus, Settings } from 'lucide-vue-next'
import LayoutPickerDropdown from './LayoutPickerDropdown.vue'

defineProps({
  showLayoutPicker: {
    type: Boolean,
    default: false
  },
  showPropertiesPanel: {
    type: Boolean,
    default: false
  },
  hasSelectedComponent: {
    type: Boolean,
    default: false
  }
})

defineEmits(['toggle-layout-picker', 'add-section', 'toggle-properties'])
</script>

<style scoped>
.canvas-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  border-bottom: 1px solid #334155;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-icon {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(6, 182, 212, 0.15) 100%);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #34d399;
}

.header-title {
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.primary {
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  border: 1px solid rgba(139, 92, 246, 0.5);
  color: white;
}

.action-btn.primary:hover {
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
}

.action-btn.secondary {
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.5);
  color: #94a3b8;
}

.action-btn.secondary:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
}

.relative {
  position: relative;
}
</style>
