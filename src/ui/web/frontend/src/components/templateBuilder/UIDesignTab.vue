<template>
  <div class="ui-design-container">
    <!-- Left: Component toolbox -->
    <ToolboxPanel
      :selected-section="selectedSection"
      :selected-column="selectedColumn"
      :search-query="searchQuery"
      :selected-category="selectedCategory"
      @add-component="$emit('add-component', $event)"
      @update:searchQuery="searchQuery = $event"
      @update:selectedCategory="selectedCategory = $event"
    />

    <!-- Right: Canvas area -->
    <CanvasPanel
      :sections="sections"
      :selected-section="selectedSection"
      :selected-column="selectedColumn"
      :selected-component-location="selectedComponentLocation"
      :show-layout-picker="showLayoutPicker"
      :show-properties-panel="showPropertiesPanel"
      @toggle-layout-picker="$emit('toggle-layout-picker')"
      @add-section="$emit('add-section', $event)"
      @select-column="handleSelectColumn"
      @select-component="handleSelectComponent"
      @open-settings="handleOpenSettings"
      @update-component="handleComponentUpdate"
      @duplicate-component="handleDuplicateComponent"
      @delete-component="handleDeleteComponent"
      @edit-grid="$emit('edit-grid', $event)"
      @move-section-up="$emit('move-section-up', $event)"
      @move-section-down="$emit('move-section-down', $event)"
      @delete-section="$emit('delete-section', $event)"
      @close-properties="$emit('close-properties')"
    >
      <template #properties-panel>
        <ComponentPropertiesPanel
          :show="showPropertiesPanel"
          :component="selectedComponentObj"
          :validation-enabled="validationEnabled"
          :select-options-text="selectOptionsText"
          :radio-options-text="radioOptionsText"
          @close="$emit('close-properties')"
          @update:validation-enabled="$emit('update:validation-enabled', $event)"
          @update:select-options="$emit('update:select-options', $event)"
          @update:radio-options="$emit('update:radio-options', $event)"
        />
      </template>
    </CanvasPanel>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ToolboxPanel from './canvas/ToolboxPanel.vue'
import CanvasPanel from './canvas/CanvasPanel.vue'
import ComponentPropertiesPanel from './ComponentPropertiesPanel.vue'

const { t } = useI18n()

const props = defineProps({
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
  selectedComponentObj: {
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
  },
  validationEnabled: {
    type: Boolean,
    default: false
  },
  selectOptionsText: {
    type: String,
    default: ''
  },
  radioOptionsText: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'add-component',
  'toggle-layout-picker',
  'add-section',
  'toggle-properties',
  'open-properties',
  'close-properties',
  'edit-grid',
  'move-section-up',
  'move-section-down',
  'delete-section',
  'select-column',
  'select-component',
  'delete-component',
  'duplicate-component',
  'update-component',
  'update:validation-enabled',
  'update:select-options',
  'update:radio-options'
])

// Local state
const searchQuery = ref('')
const selectedCategory = ref(t('templateBuilder.categories.all'))

// Handler for selecting a column
function handleSelectColumn(sectionIndex, columnIndex) {
  emit('select-column', sectionIndex, columnIndex)
}

// Handler for selecting a component
function handleSelectComponent(sectionIndex, columnIndex, componentIndex) {
  emit('select-component', sectionIndex, columnIndex, componentIndex)
}

// Handler for opening settings panel - directly opens, not toggle
function handleOpenSettings(sectionIndex, columnIndex, componentIndex) {
  emit('select-component', sectionIndex, columnIndex, componentIndex)
  emit('open-properties')
}

// Handler for component updates from direct editing
function handleComponentUpdate(payload) {
  emit('update-component', payload)
}

// Handler for duplicating a component
function handleDuplicateComponent(sectionIndex, columnIndex, componentIndex) {
  emit('duplicate-component', sectionIndex, columnIndex, componentIndex)
}

// Handler for deleting a component
function handleDeleteComponent(sectionIndex, columnIndex, componentIndex) {
  emit('delete-component', sectionIndex, columnIndex, componentIndex)
}
</script>

<style scoped>
.ui-design-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}
</style>
