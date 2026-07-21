<template>
  <div class="section-toolbar">
    <div class="section-info">
      <div class="section-icon">
        <LayoutGrid :size="14" />
      </div>
      <span class="section-label">{{ $t('templateBuilder.section.layout', { columns }) }}</span>
      <span class="section-grid-info">({{ gridInfo }}/12)</span>
    </div>
    <div class="section-actions">
      <button
        @click="$emit('edit-grid')"
        class="section-action-btn"
        :title="$t('templateBuilder.section.setRatio')"
      >
        <Settings :size="14" />
      </button>
      <button
        @click="$emit('move-up')"
        :disabled="isFirst"
        class="section-action-btn"
        :title="$t('templateBuilder.section.moveUp')"
      >
        <ChevronUp :size="14" />
      </button>
      <button
        @click="$emit('move-down')"
        :disabled="isLast"
        class="section-action-btn"
        :title="$t('templateBuilder.section.moveDown')"
      >
        <ChevronDown :size="14" />
      </button>
      <button
        @click="$emit('delete')"
        class="section-action-btn delete-btn"
        :title="$t('templateBuilder.section.deleteSection')"
      >
        <Trash2 :size="14" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { LayoutGrid, Settings, ChevronUp, ChevronDown, Trash2 } from 'lucide-vue-next'

const props = defineProps({
  columns: {
    type: Number,
    required: true
  },
  grid: {
    type: Array,
    required: true
  },
  isFirst: {
    type: Boolean,
    default: false
  },
  isLast: {
    type: Boolean,
    default: false
  }
})

defineEmits(['edit-grid', 'move-up', 'move-down', 'delete'])

const gridInfo = computed(() => props.grid.join('+'))
</script>

<style scoped>
.section-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(30, 41, 59, 0.8);
  border-bottom: 1px solid #334155;
}

.section-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-icon {
  color: #8B5CF6;
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: #f1f5f9;
}

.section-grid-info {
  font-size: 11px;
  color: #64748b;
  font-family: monospace;
}

.section-actions {
  display: flex;
  gap: 4px;
}

.section-action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: none;
  background: rgba(71, 85, 105, 0.3);
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.section-action-btn:hover:not(:disabled) {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
}

.section-action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.section-action-btn.delete-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}
</style>
