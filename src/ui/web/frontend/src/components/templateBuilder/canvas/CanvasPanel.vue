<template>
  <div class="canvas-panel">
    <CanvasHeader
      :show-layout-picker="showLayoutPicker"
      @toggle-layout-picker="$emit('toggle-layout-picker')"
      @add-section="$emit('add-section', $event)"
    />

    <div class="canvas-content custom-scrollbar">
      <div v-if="sections.length > 0" class="sections-container">
        <SectionBlock
          v-for="(section, sIndex) in sections"
          :key="section.id"
          :section="section"
          :section-index="sIndex"
          :is-selected="selectedSection === sIndex"
          :selected-column="selectedSection === sIndex ? selectedColumn : null"
          :selected-component-location="selectedComponentLocation"
          :is-first="sIndex === 0"
          :is-last="sIndex === sections.length - 1"
          @select-column="$emit('select-column', sIndex, $event)"
          @select-component="$emit('select-component', sIndex, $event.columnIndex, $event.componentIndex)"
          @open-settings="$emit('open-settings', sIndex, $event.columnIndex, $event.componentIndex)"
          @update-component="$emit('update-component', { sectionIndex: sIndex, ...$event })"
          @duplicate-component="$emit('duplicate-component', sIndex, $event.columnIndex, $event.componentIndex)"
          @delete-component="$emit('delete-component', sIndex, $event.columnIndex, $event.componentIndex)"
          @edit-grid="$emit('edit-grid', sIndex)"
          @move-up="$emit('move-section-up', sIndex)"
          @move-down="$emit('move-section-down', sIndex)"
          @delete="$emit('delete-section', sIndex)"
        />
      </div>

      <CanvasEmptyState v-else />
    </div>

    <!-- Background overlay for properties panel -->
    <div
      v-if="showPropertiesPanel"
      @click="$emit('close-properties')"
      class="properties-overlay"
    ></div>

    <!-- Properties panel slot -->
    <slot name="properties-panel"></slot>
  </div>
</template>

<script setup>
import CanvasHeader from '../CanvasHeader.vue'
import CanvasEmptyState from './panel/CanvasEmptyState.vue'
import SectionBlock from './panel/SectionBlock.vue'

defineProps({
  sections: {
    type: Array,
    required: true
  },
  selectedSection: {
    type: Number,
    default: null
  },
  selectedColumn: {
    type: Number,
    default: null
  },
  selectedComponentLocation: {
    type: Object,
    default: null
  },
  showLayoutPicker: {
    type: Boolean,
    default: false
  },
  showPropertiesPanel: {
    type: Boolean,
    default: false
  }
})

defineEmits([
  'toggle-layout-picker',
  'add-section',
  'select-column',
  'select-component',
  'open-settings',
  'update-component',
  'duplicate-component',
  'delete-component',
  'edit-grid',
  'move-section-up',
  'move-section-down',
  'delete-section',
  'close-properties'
])
</script>

<style scoped>
.canvas-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #0f172a;
}

.canvas-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.sections-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.properties-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  transition: opacity 0.3s;
  z-index: 40;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}
</style>
