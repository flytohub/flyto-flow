<template>
  <div
    class="section-block"
    :class="{ 'section-selected': isSelected }"
  >
    <!-- Section toolbar -->
    <div class="section-toolbar">
      <div class="section-info">
        <div class="section-icon">
          <LayoutGrid :size="14" />
        </div>
        <span class="section-label">{{ $t('templateBuilder.section.layout', { columns: section.columns }) }}</span>
        <span class="section-grid-info">({{ (section.grid || []).join('+') }}/12)</span>
      </div>
      <div class="section-actions">
        <button
          @click="$emit('editGrid')"
          class="section-action-btn"
          :title="$t('templateBuilder.section.setRatio')"
        >
          <Settings :size="14" />
        </button>
        <button
          @click="$emit('moveUp')"
          :disabled="isFirst"
          class="section-action-btn"
          :title="$t('templateBuilder.section.moveUp')"
        >
          <ChevronUp :size="14" />
        </button>
        <button
          @click="$emit('moveDown')"
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

    <!-- Column grid -->
    <div
      class="section-columns"
      :style="{
        display: 'grid',
        gridTemplateColumns: calculateGridTemplate(section.grid),
        gap: section.gap
      }"
    >
      <!-- Iterate through columns -->
      <div
        v-for="(column, cIndex) in section.columnsData"
        :key="`col-${sectionIndex}-${cIndex}`"
        class="column-drop-zone"
        :class="{
          'column-selected': selectedColumn === cIndex && isSelected
        }"
        @click="$emit('selectColumn', cIndex)"
      >
        <!-- Column placeholder -->
        <div v-if="column.components.length === 0" class="column-empty">
          <Plus :size="28" />
          <p class="empty-title">{{ $t('templateBuilder.section.clickToSelect') }}</p>
          <p class="empty-hint">{{ $t('templateBuilder.section.addComponentsFromLeft') }}</p>
        </div>

        <!-- Iterate through components -->
        <div
          v-for="(comp, compIndex) in column.components"
          :key="comp.id"
          class="placed-component"
          :class="{
            'component-selected': isComponentSelected(cIndex, compIndex)
          }"
          @click.stop="$emit('selectComponent', { columnIndex: cIndex, componentIndex: compIndex })"
        >
          <div class="flex items-start justify-between mb-2">
            <div class="flex items-center gap-2 flex-1 min-w-0">
              <component :is="getComponentIcon(comp.type)" :size="16" class="text-primary-600 flex-shrink-0" />
              <span class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{{ comp.label }}</span>
            </div>
            <button
              @click.stop="$emit('deleteComponent', { columnIndex: cIndex, componentIndex: compIndex })"
              class="p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900 rounded transition-all"
              :title="$t('common.delete')"
            >
              <X :size="14" />
            </button>
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400 font-mono">{{ comp.id }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  LayoutGrid, Settings, ChevronUp, ChevronDown, Trash2, Plus, X,
  Type, FileType, ChevronDown as ChevronDownIcon, SquareCheck, CircleDot, ToggleLeft,
  Calendar, Clock, Sliders, Star, Upload,
  Heading1, AlignLeft, Minus, RectangleHorizontal,
  Mail, Lock, Link, Hash, Package
} from 'lucide-vue-next'

const props = defineProps({
  section: {
    type: Object,
    required: true
  },
  sectionIndex: {
    type: Number,
    required: true
  },
  isSelected: {
    type: Boolean,
    default: false
  },
  selectedColumn: {
    type: Number,
    default: null
  },
  selectedComponentLocation: {
    type: Object,
    default: null
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

defineEmits(['selectColumn', 'selectComponent', 'deleteComponent', 'editGrid', 'moveUp', 'moveDown', 'delete'])

// Calculate Grid column width (12 column grid system)
function calculateGridTemplate(gridArray) {
  return (gridArray || []).map(cols => `${cols}fr`).join(' ')
}

// Check if component is selected
function isComponentSelected(columnIndex, componentIndex) {
  return props.selectedComponentLocation &&
    props.selectedComponentLocation.sectionIndex === props.sectionIndex &&
    props.selectedComponentLocation.columnIndex === columnIndex &&
    props.selectedComponentLocation.componentIndex === componentIndex
}

// Component icon map
const componentIconMap = {
  input: Type,
  email: Mail,
  password: Lock,
  number: Hash,
  url: Link,
  tel: Type,
  textarea: FileType,
  select: ChevronDownIcon,
  checkbox: SquareCheck,
  radio: CircleDot,
  switch: ToggleLeft,
  date: Calendar,
  time: Clock,
  range: Sliders,
  rating: Star,
  file: Upload,
  heading: Heading1,
  text: AlignLeft,
  divider: Minus,
  button: RectangleHorizontal
}

function getComponentIcon(type) {
  return componentIconMap[type] || Package
}
</script>

<style scoped>
.section-block {
  background: linear-gradient(135deg, #0c1222 0%, #070b14 100%);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.section-block:hover {
  border-color: rgba(139, 92, 246, 0.4);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.section-block.section-selected {
  border-color: rgba(139, 92, 246, 0.7);
  box-shadow:
    0 0 30px rgba(139, 92, 246, 0.2),
    0 12px 40px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(139, 92, 246, 0.1);
}

/* Section Toolbar */
.section-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(90deg, rgba(139, 92, 246, 0.08) 0%, rgba(6, 182, 212, 0.04) 100%);
  border-bottom: 1px solid rgba(71, 85, 105, 0.4);
}

.section-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  color: #a78bfa;
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
}

.section-grid-info {
  font-size: 11px;
  font-family: 'SF Mono', Monaco, monospace;
  color: #64748b;
  background: rgba(71, 85, 105, 0.3);
  padding: 2px 8px;
  border-radius: 4px;
}

/* Section Action Buttons */
.section-actions {
  display: flex;
  gap: 4px;
}

.section-action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(71, 85, 105, 0.2);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 8px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.section-action-btn:hover:not(:disabled) {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
  color: #c4b5fd;
  box-shadow: 0 0 12px rgba(139, 92, 246, 0.3);
}

.section-action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.section-action-btn.delete-btn {
  color: #f87171;
}

.section-action-btn.delete-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.5);
  color: #fca5a5;
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.3);
}

/* Section Columns Area */
.section-columns {
  padding: 16px;
}

/* Column Drop Zone */
.column-drop-zone {
  min-height: 160px;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(7, 11, 20, 0.8) 100%);
  border: 2px dashed rgba(71, 85, 105, 0.5);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.column-drop-zone:hover {
  border-color: rgba(139, 92, 246, 0.5);
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(15, 23, 42, 0.6) 100%);
}

.column-drop-zone.column-selected {
  border-style: solid;
  border-color: #8B5CF6;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(15, 23, 42, 0.8) 100%);
  box-shadow:
    0 0 20px rgba(139, 92, 246, 0.2),
    inset 0 0 30px rgba(139, 92, 246, 0.05);
}

/* Column Empty State */
.column-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 120px;
  color: #64748b;
}

.column-empty svg {
  color: #475569;
  margin-bottom: 12px;
}

.column-empty .empty-title {
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
  margin: 0 0 4px 0;
}

.column-empty .empty-hint {
  font-size: 11px;
  color: #64748b;
  margin: 0;
}

.column-selected .column-empty svg {
  color: #8B5CF6;
}

.column-selected .column-empty .empty-title {
  color: #c4b5fd;
}

/* Placed Component in Column */
.placed-component {
  margin-bottom: 12px;
  padding: 14px;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 10px;
  transition: all 0.2s;
}

.placed-component:last-child {
  margin-bottom: 0;
}

.placed-component:hover {
  border-color: rgba(139, 92, 246, 0.4);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.placed-component.component-selected {
  border-color: #10B981;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(15, 23, 42, 0.9) 100%);
  box-shadow:
    0 0 20px rgba(16, 185, 129, 0.2),
    0 4px 16px rgba(0, 0, 0, 0.3);
}

/* Fix text colors inside placed components */
.placed-component .text-gray-900,
.placed-component :deep(.text-gray-100) {
  color: #e2e8f0 !important;
}

.placed-component .text-primary-600 {
  color: #a78bfa !important;
}
</style>
