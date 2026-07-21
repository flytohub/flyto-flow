<template>
  <div
    class="column-drop-zone"
    :class="{ 'column-selected': isSelected }"
    @click="$emit('select')"
  >
    <EmptyColumnState v-if="column.components.length === 0" />

    <PlacedComponentWrapper
      v-for="(comp, compIndex) in column.components"
      :key="comp.id"
      :component="comp"
      :is-selected="isComponentSelected(compIndex)"
      :editable="true"
      :show-duplicate-action="true"
      :show-delete-action="true"
      @select="$emit('select-component', compIndex)"
      @open-settings="$emit('open-settings', compIndex)"
      @update="$emit('update-component', { componentIndex: compIndex, ...$event })"
      @duplicate="$emit('duplicate-component', compIndex)"
      @delete="$emit('delete-component', compIndex)"
    />
  </div>
</template>

<script setup>
import EmptyColumnState from './EmptyColumnState.vue'
import PlacedComponentWrapper from '../component/PlacedComponentWrapper.vue'

const props = defineProps({
  column: {
    type: Object,
    required: true
  },
  columnIndex: {
    type: Number,
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
  selectedComponentLocation: {
    type: Object,
    default: null
  }
})

defineEmits([
  'select',
  'select-component',
  'open-settings',
  'update-component',
  'duplicate-component',
  'delete-component'
])

function isComponentSelected(componentIndex) {
  return props.selectedComponentLocation &&
    props.selectedComponentLocation.sectionIndex === props.sectionIndex &&
    props.selectedComponentLocation.columnIndex === props.columnIndex &&
    props.selectedComponentLocation.componentIndex === componentIndex
}
</script>

<style scoped>
.column-drop-zone {
  min-height: 120px;
  border: 2px dashed #334155;
  border-radius: 10px;
  padding: 12px;
  transition: all 0.2s;
  cursor: pointer;
}

.column-drop-zone:hover {
  border-color: #475569;
  background: rgba(71, 85, 105, 0.1);
}

.column-drop-zone.column-selected {
  border-color: #8B5CF6;
  border-style: solid;
  background: rgba(139, 92, 246, 0.05);
}
</style>
