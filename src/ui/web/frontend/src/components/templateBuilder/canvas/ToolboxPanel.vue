<template>
  <div class="toolbox-panel">
    <ToolboxHeader :selected-section="selectedSection" :selected-column="selectedColumn" />
    <ToolboxSearch v-model="searchQueryModel" />
    <CategoryFilter
      :categories="componentCategories"
      :selected-category="selectedCategoryModel"
      @select="selectedCategoryModel = $event"
    />
    <div class="component-list custom-scrollbar">
      <EmptyToolboxState v-if="selectedSection === null || selectedColumn === null" />
      <ComponentGrid
        v-else
        :components="filteredComponents"
        @add-component="$emit('add-component', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import ToolboxHeader from '../ToolboxHeader.vue'
import ToolboxSearch from '../ToolboxSearch.vue'
import CategoryFilter from '../CategoryFilter.vue'
import EmptyToolboxState from './toolbox/EmptyToolboxState.vue'
import ComponentGrid from './toolbox/ComponentGrid.vue'
import { useComponentCatalog } from '../composables/useComponentCatalog'

const { t } = useI18n()

const props = defineProps({
  selectedSection: {
    type: Number,
    default: null
  },
  selectedColumn: {
    type: Number,
    default: null
  },
  searchQuery: {
    type: String,
    default: ''
  },
  selectedCategory: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['add-component', 'update:searchQuery', 'update:selectedCategory'])

const searchQueryModel = computed({
  get: () => props.searchQuery,
  set: (val) => emit('update:searchQuery', val)
})

const selectedCategoryModel = computed({
  get: () => props.selectedCategory || t('templateBuilder.categories.all'),
  set: (val) => emit('update:selectedCategory', val)
})

const { availableComponents, componentCategories, filterComponents } = useComponentCatalog()

const filteredComponents = computed(() => {
  return filterComponents(searchQueryModel.value, selectedCategoryModel.value)
})
</script>

<style scoped>
.toolbox-panel {
  width: 320px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  border-right: 1px solid #334155;
  overflow: hidden;
}

.component-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
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
