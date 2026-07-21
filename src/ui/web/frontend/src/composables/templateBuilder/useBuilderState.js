/**
 * Builder State Composable
 *
 * Wraps builderStore state with computed getters/setters.
 * Reduces boilerplate in TemplateBuilder.vue from ~200 lines to ~10 lines.
 */

import { computed } from 'vue'
import { useBuilderStore } from '@/stores/builderStore'
import { useI18n } from 'vue-i18n'

/**
 * Create computed wrapper for store property
 */
function storeComputed(store, key) {
  return computed({
    get: () => store[key],
    set: (v) => { store[key] = v }
  })
}

/**
 * Use builder state - all reactive state from builderStore
 */
export function useBuilderState() {
  const builderStore = useBuilderStore()
  const { t } = useI18n()

  // Tab state
  const activeTab = storeComputed(builderStore, 'activeTab')
  const showTerminal = storeComputed(builderStore, 'showTerminal')

  // Template info
  const templateName = storeComputed(builderStore, 'templateName')
  const templateId = storeComputed(builderStore, 'templateId')
  const templateDescription = storeComputed(builderStore, 'templateDescription')
  const existingTemplateId = storeComputed(builderStore, 'existingTemplateId')
  const templateCreatorId = storeComputed(builderStore, 'templateCreatorId')
  const templateMutability = storeComputed(builderStore, 'templateMutability')
  const templateVisibility = storeComputed(builderStore, 'templateVisibility')
  const templateListed = storeComputed(builderStore, 'templateListed')
  const isWorkflowVisible = storeComputed(builderStore, 'isWorkflowVisible')

  // Editing state
  const hasUnsavedChanges = storeComputed(builderStore, 'hasUnsavedChanges')
  const isSaving = storeComputed(builderStore, 'isSaving')
  const isLoadingTemplate = storeComputed(builderStore, 'isLoading')
  const loadError = storeComputed(builderStore, 'loadError')
  const sections = storeComputed(builderStore, 'sections')
  const autoSaveEnabled = storeComputed(builderStore, 'autoSaveEnabled')

  // UI state
  const showLayoutPicker = storeComputed(builderStore, 'showLayoutPicker')
  const showGridEditDialog = storeComputed(builderStore, 'showGridEditDialog')
  const showPropertiesPanel = storeComputed(builderStore, 'showPropertiesPanel')
  const showSaveDialog = storeComputed(builderStore, 'showSaveDialog')
  const showTestModal = storeComputed(builderStore, 'showTestModal')
  const showSettingsPanel = storeComputed(builderStore, 'showSettingsPanel')
  const nodePropertiesCollapsed = storeComputed(builderStore, 'nodePropertiesCollapsed')

  // Selection state
  const selectedSection = storeComputed(builderStore, 'selectedSection')
  const selectedColumn = storeComputed(builderStore, 'selectedColumn')
  const selectedComponentLocation = storeComputed(builderStore, 'selectedComponentLocation')

  // Grid editing
  const tempGridValues = storeComputed(builderStore, 'tempGridValues')
  const editingGridSection = storeComputed(builderStore, 'editingGridSection')

  // Initialize template name with i18n default if empty
  if (!templateName.value) {
    templateName.value = t('templateBuilder.toolbar.templateNamePlaceholder')
  }

  // Computed template data object
  // Returns deep copy to prevent external mutation of internal state
  const templateData = computed(() => {
    const sectionsData = sections.value
    return {
      templateId: templateId.value,
      name: templateName.value,
      description: templateDescription.value,
      version: '1.0',
      ui: {
        // Deep copy sections to prevent state pollution
        sections: sectionsData ? JSON.parse(JSON.stringify(sectionsData)) : []
      }
    }
  })

  // Selected component object with comprehensive null checks
  const selectedComponentObj = computed(() => {
    const location = selectedComponentLocation.value
    if (!location) return null

    // Validate location indices are valid numbers
    const { sectionIndex, columnIndex, componentIndex } = location
    if (typeof sectionIndex !== 'number' ||
        typeof columnIndex !== 'number' ||
        typeof componentIndex !== 'number') {
      return null
    }

    // Validate indices are non-negative
    if (sectionIndex < 0 || columnIndex < 0 || componentIndex < 0) {
      return null
    }

    // Safely traverse the data structure
    const sectionsData = sections.value
    if (!Array.isArray(sectionsData) || sectionIndex >= sectionsData.length) {
      return null
    }

    const section = sectionsData[sectionIndex]
    if (!section?.columnsData || !Array.isArray(section.columnsData)) {
      return null
    }

    if (columnIndex >= section.columnsData.length) {
      return null
    }

    const column = section.columnsData[columnIndex]
    if (!column?.components || !Array.isArray(column.components)) {
      return null
    }

    if (componentIndex >= column.components.length) {
      return null
    }

    return column.components[componentIndex] || null
  })

  // Read-only check
  const isReadOnly = computed(() => {
    // Template is read-only if user is not the creator
    // and template mutability is 'immutable'
    return templateMutability.value === 'immutable' &&
           templateCreatorId.value !== builderStore.currentUserId
  })

  return {
    // Store reference
    builderStore,

    // Tab state
    activeTab,
    showTerminal,

    // Template info
    templateName,
    templateId,
    templateDescription,
    existingTemplateId,
    templateCreatorId,
    templateMutability,
    templateVisibility,
    templateListed,
    isWorkflowVisible,

    // Editing state
    hasUnsavedChanges,
    isSaving,
    isLoadingTemplate,
    loadError,
    sections,
    autoSaveEnabled,

    // UI state
    showLayoutPicker,
    showGridEditDialog,
    showPropertiesPanel,
    showSaveDialog,
    showTestModal,
    showSettingsPanel,
    nodePropertiesCollapsed,

    // Selection state
    selectedSection,
    selectedColumn,
    selectedComponentLocation,

    // Grid editing
    tempGridValues,
    editingGridSection,

    // Computed
    templateData,
    selectedComponentObj,
    isReadOnly,
  }
}

export default useBuilderState
