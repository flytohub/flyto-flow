/**
 * Builder UI State Store
 * Manages panel visibility, mode, and selection state
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useBuilderUIStore = defineStore('builder-ui', () => {
  // ========== Mode State ==========
  const activeTab = ref('ui')
  const builderMode = ref('dev') // 'dev' | 'preview'

  // ========== Panel Visibility ==========
  const showTerminal = ref(false)
  const showLayoutPicker = ref(false)
  const showPropertiesPanel = ref(false)
  const showModuleSelector = ref(false)
  const isAddingFirstNode = ref(false)  // True when adding a starter node
  const showSaveDialog = ref(false)
  const showTestModal = ref(false)
  const showGridEditDialog = ref(false)
  const nodePropertiesCollapsed = ref(false)
  const showSettingsPanel = ref(false)

  // ========== Selection State ==========
  const selectedSection = ref(null)
  const selectedColumn = ref(null)
  const selectedComponentLocation = ref(null)

  // ========== Getters ==========
  const isDev = computed(() => builderMode.value === 'dev')
  const isPreview = computed(() => builderMode.value === 'preview')

  // ========== Mode Actions ==========
  function setActiveTab(tab) {
    activeTab.value = tab
  }

  function setBuilderMode(mode) {
    builderMode.value = mode
  }

  // ========== Panel Toggle Actions ==========
  function toggleTerminal() {
    showTerminal.value = !showTerminal.value
  }

  function setShowPropertiesPanel(show) {
    showPropertiesPanel.value = show
  }

  function setShowLayoutPicker(show) {
    showLayoutPicker.value = show
  }

  function setShowModuleSelector(show, isFirst = false) {
    showModuleSelector.value = show
    isAddingFirstNode.value = show && isFirst
  }

  function setShowSaveDialog(show) {
    showSaveDialog.value = show
  }

  function setShowTestModal(show) {
    showTestModal.value = show
  }

  function setShowGridEditDialog(show) {
    showGridEditDialog.value = show
  }

  function setNodePropertiesCollapsed(collapsed) {
    nodePropertiesCollapsed.value = collapsed
  }

  function setShowSettingsPanel(show) {
    showSettingsPanel.value = show
  }

  // ========== Selection Actions ==========
  function selectSection(sectionIndex) {
    selectedSection.value = sectionIndex
    selectedColumn.value = null
    selectedComponentLocation.value = null
  }

  function selectColumn(sectionIndex, columnIndex) {
    selectedSection.value = sectionIndex
    selectedColumn.value = columnIndex
    selectedComponentLocation.value = null
  }

  function selectComponent(sectionIndex, columnIndex, componentIndex) {
    selectedComponentLocation.value = { sectionIndex, columnIndex, componentIndex }
    showPropertiesPanel.value = true
  }

  function clearSelection() {
    selectedSection.value = null
    selectedColumn.value = null
    selectedComponentLocation.value = null
    showPropertiesPanel.value = false
  }

  function clearComponentSelectionOnDelete(location) {
    if (selectedComponentLocation.value?.sectionIndex === location.sectionIndex &&
        selectedComponentLocation.value?.columnIndex === location.columnIndex &&
        selectedComponentLocation.value?.componentIndex === location.componentIndex) {
      selectedComponentLocation.value = null
      showPropertiesPanel.value = false
    }
  }

  function updateSelectedSectionOnMove(fromIndex, toIndex) {
    if (selectedSection.value === fromIndex) {
      selectedSection.value = toIndex
    }
  }

  function clearSectionSelectionOnDelete(index) {
    if (selectedSection.value === index) {
      selectedSection.value = null
      selectedColumn.value = null
      selectedComponentLocation.value = null
    }
  }

  // ========== Reset ==========
  function reset() {
    activeTab.value = 'ui'
    builderMode.value = 'dev'
    showTerminal.value = false
    showLayoutPicker.value = false
    showPropertiesPanel.value = false
    showModuleSelector.value = false
    isAddingFirstNode.value = false
    showSaveDialog.value = false
    showTestModal.value = false
    showGridEditDialog.value = false
    nodePropertiesCollapsed.value = false
    showSettingsPanel.value = false
    selectedSection.value = null
    selectedColumn.value = null
    selectedComponentLocation.value = null
  }

  return {
    // Mode State
    activeTab,
    builderMode,

    // Panel Visibility
    showTerminal,
    showLayoutPicker,
    showPropertiesPanel,
    showModuleSelector,
    isAddingFirstNode,
    showSaveDialog,
    showTestModal,
    showGridEditDialog,
    nodePropertiesCollapsed,
    showSettingsPanel,

    // Selection State
    selectedSection,
    selectedColumn,
    selectedComponentLocation,

    // Getters
    isDev,
    isPreview,

    // Mode Actions
    setActiveTab,
    setBuilderMode,

    // Panel Toggle Actions
    toggleTerminal,
    setShowPropertiesPanel,
    setShowLayoutPicker,
    setShowModuleSelector,
    setShowSaveDialog,
    setShowTestModal,
    setShowGridEditDialog,
    setNodePropertiesCollapsed,
    setShowSettingsPanel,

    // Selection Actions
    selectSection,
    selectColumn,
    selectComponent,
    clearSelection,
    clearComponentSelectionOnDelete,
    updateSelectedSectionOnMove,
    clearSectionSelectionOnDelete,

    // Reset
    reset
  }
})
