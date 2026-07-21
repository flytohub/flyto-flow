<template>
  <div class="layout-picker" @click.stop>
    <div class="picker-header">
      <h4>{{ $t('templateBuilder.canvas.selectColumns') }}</h4>
    </div>
    <div class="picker-options">
      <button
        v-for="cols in columnOptions"
        :key="cols"
        @click="$emit('select', cols)"
        class="layout-option"
      >
        <component :is="getColumnIcon(cols)" :size="18" />
        <span>{{ $t('templateBuilder.canvas.columnsLayout', { cols }) }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import {
  RectangleVertical,
  Columns2 as Columns2Icon,
  Columns3,
  Columns4
} from 'lucide-vue-next'

const columnOptions = [1, 2, 3, 4]

defineEmits(['select'])

function getColumnIcon(cols) {
  const icons = {
    1: RectangleVertical,
    2: Columns2Icon,
    3: Columns3,
    4: Columns4
  }
  return icons[cols] || RectangleVertical
}
</script>

<style scoped>
.layout-picker {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  min-width: 240px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
  z-index: 100;
}

.picker-header {
  padding: 14px 16px;
  border-bottom: 1px solid #334155;
}

.picker-header h4 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #f1f5f9;
  white-space: nowrap;
}

.picker-options {
  padding: 8px;
}

.layout-option {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 10px 12px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.layout-option:hover {
  background: rgba(139, 92, 246, 0.15);
  color: #A78BFA;
}
</style>
