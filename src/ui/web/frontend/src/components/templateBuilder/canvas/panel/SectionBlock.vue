<template>
  <div
    class="section-block"
    :class="{ 'section-selected': isSelected }"
  >
    <SectionToolbar
      :columns="section.columns"
      :grid="section.grid"
      :is-first="isFirst"
      :is-last="isLast"
      @edit-grid="$emit('edit-grid')"
      @move-up="$emit('move-up')"
      @move-down="$emit('move-down')"
      @delete="$emit('delete')"
    />

    <div
      class="section-columns"
      :style="{
        display: 'grid',
        gridTemplateColumns: calculateGridTemplate(section.grid),
        gap: section.gap
      }"
    >
      <ColumnContainer
        v-for="(column, cIndex) in section.columnsData"
        :key="`col-${sectionIndex}-${cIndex}`"
        :column="column"
        :column-index="cIndex"
        :is-selected="selectedColumn === cIndex"
        :selected-component-location="selectedComponentLocation"
        :section-index="sectionIndex"
        @select="$emit('select-column', cIndex)"
        @select-component="$emit('select-component', { columnIndex: cIndex, componentIndex: $event })"
        @open-settings="$emit('open-settings', { columnIndex: cIndex, componentIndex: $event })"
        @update-component="$emit('update-component', { columnIndex: cIndex, ...$event })"
        @duplicate-component="$emit('duplicate-component', { columnIndex: cIndex, componentIndex: $event })"
        @delete-component="$emit('delete-component', { columnIndex: cIndex, componentIndex: $event })"
      />
    </div>
  </div>
</template>

<script setup>
import SectionToolbar from '../../SectionToolbar.vue'
import ColumnContainer from './ColumnContainer.vue'

defineProps({
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

defineEmits([
  'select-column',
  'select-component',
  'open-settings',
  'update-component',
  'duplicate-component',
  'delete-component',
  'edit-grid',
  'move-up',
  'move-down',
  'delete'
])

function calculateGridTemplate(gridArray) {
  return (gridArray || []).map(cols => `${cols}fr`).join(' ')
}
</script>

<style scoped>
.section-block {
  border: 1px solid #334155;
  border-radius: 12px;
  background: rgba(30, 41, 59, 0.5);
  transition: all 0.2s;
}

.section-block.section-selected {
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.section-columns {
  padding: 16px;
}
</style>
