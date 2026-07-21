<template>
  <div class="variable-selector" :class="{ inline: mode === 'inline' }">
    <VariableTabs
      v-model:activeTab="activeTab"
      :available-variables="availableVariables"
    />

    <VariableSearch
      v-model="searchQuery"
      @clear="clearSearch"
    />

    <VariableList
      :variables="filteredVariables"
      :selected-path="selectedVariable?.path"
      @select="selectVariable"
    />

    <VariableFooter
      :show="mode === 'popup' && !!selectedVariable"
      :expression="selectedVariable?.expression || ''"
      @confirm="confirmSelection"
    />
  </div>
</template>

<script setup>
import { VariableTabs, VariableSearch, VariableList, VariableFooter, useVariableSelector } from './variableSelector'

const props = defineProps({
  availableVariables: {
    type: Object,
    default: () => ({ inputs: [], steps: [], env: [] })
  },
  filterTypes: {
    type: [String, Array],
    default: null
  },
  mode: {
    type: String,
    default: 'popup',
    validator: v => ['popup', 'inline'].includes(v)
  },
  modelValue: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['select', 'update:modelValue'])

const {
  activeTab,
  searchQuery,
  selectedVariable,
  filteredVariables,
  selectVariable,
  confirmSelection,
  clearSearch
} = useVariableSelector(props, emit)
</script>

<style scoped>
.variable-selector {
  display: flex;
  flex-direction: column;
  background: linear-gradient(145deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 12px;
  overflow: hidden;
  min-width: 280px;
  max-width: 360px;
  max-height: 400px;
  backdrop-filter: blur(12px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.variable-selector.inline {
  max-height: none;
  border-radius: 8px;
  box-shadow: none;
}
</style>
