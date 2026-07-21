/**
 * Component CRUD Actions
 *
 * S-Grade: Component CRUD operations.
 * Single responsibility: Add, delete, duplicate, update components.
 */

import { applyDefaultConfig, isFormType } from './defaultConfig'

/**
 * Create component CRUD actions
 * @param {Object} options - Options from useComponentManager
 * @param {Object} counter - Component counter ref object
 * @param {Function} t - i18n translate function
 * @returns {Object} CRUD action functions
 */
export function createCrudActions(options, counter, t) {
  const {
    sections,
    selectedSection,
    selectedColumn,
    selectedComponentLocation,
    showPropertiesPanel,
    hasUnsavedChanges,
    showConfirm,
    showToast
  } = options

  /**
   * Select a component
   */
  function selectComponent(sectionIndex, columnIndex, componentIndex) {
    selectedComponentLocation.value = { sectionIndex, columnIndex, componentIndex }
    showPropertiesPanel.value = true
  }

  /**
   * Add a component to the selected column
   * FE-P1-010: Added null checks for section and column
   */
  function addComponentToColumn(type) {
    if (selectedSection.value === null || selectedColumn.value === null) {
      showToast(t('templateBuilder.alerts.selectColumnFirst'), 'warning')
      return
    }

    const section = sections.value[selectedSection.value]
    if (!section || !section.columnsData) {
      showToast(t('templateBuilder.alerts.selectColumnFirst'), 'warning')
      return
    }

    const column = section.columnsData[selectedColumn.value]
    if (!column || !column.components) {
      showToast(t('templateBuilder.alerts.selectColumnFirst'), 'warning')
      return
    }

    const formType = isFormType(type)

    const newComponent = {
      type,
      id: `${type}_${counter.value++}`,
      label: `${type.charAt(0).toUpperCase() + type.slice(1)} ${counter.value - 1}`,
      // Add module for form types so they appear in Parameter Settings
      ...(formType && { module: `form.${type}` }),
      // Add params with variableName for workflow reference
      ...(formType && { params: { variableName: `${type}_${counter.value - 1}` } })
    }

    applyDefaultConfig(type, newComponent)

    // Use array spread to ensure Vue reactivity (avoid direct mutation)
    column.components = [...column.components, newComponent]
    selectComponent(selectedSection.value, selectedColumn.value, column.components.length - 1)
    hasUnsavedChanges.value = true
  }

  /**
   * Delete a component
   */
  async function deleteComponent(sectionIndex, columnIndex, componentIndex) {
    const confirmed = await showConfirm({
      type: 'danger',
      title: t('templateBuilder.dialog.deleteComponent'),
      message: t('templateBuilder.dialog.confirmDeleteComponent'),
      confirmText: t('common.delete')
    })

    if (confirmed) {
      const section = sections.value[sectionIndex]
      const column = section.columnsData[columnIndex]
      // Use filter to create new array (avoid direct mutation with splice)
      column.components = column.components.filter((_, idx) => idx !== componentIndex)

      if (selectedComponentLocation.value &&
          selectedComponentLocation.value.sectionIndex === sectionIndex &&
          selectedComponentLocation.value.columnIndex === columnIndex &&
          selectedComponentLocation.value.componentIndex === componentIndex) {
        selectedComponentLocation.value = null
        showPropertiesPanel.value = false
      }

      hasUnsavedChanges.value = true
      showToast(t('templateBuilder.toast.componentDeleted'), 'success')
    }
  }

  /**
   * Duplicate a component
   * FE-P1-009: Ensure duplicated component has unique variableName
   */
  function duplicateComponent(sectionIndex, columnIndex, componentIndex) {
    const section = sections.value[sectionIndex]
    if (!section) return

    const column = section.columnsData[columnIndex]
    if (!column) return

    const originalComponent = column.components[componentIndex]
    if (!originalComponent) return

    // Create a deep copy with a new ID
    const newComponent = JSON.parse(JSON.stringify(originalComponent))
    const newId = `${originalComponent.type}_${counter.value++}`
    newComponent.id = newId
    newComponent.label = `${originalComponent.label} (Copy)`

    // FE-P1-009: Generate unique variableName to prevent collisions
    if (newComponent.params && newComponent.params.variableName) {
      newComponent.params.variableName = `${originalComponent.type}_${counter.value - 1}`
    }

    // Insert after the original component (avoid direct mutation with splice)
    column.components = [
      ...column.components.slice(0, componentIndex + 1),
      newComponent,
      ...column.components.slice(componentIndex + 1)
    ]

    // Select the new component
    selectComponent(sectionIndex, columnIndex, componentIndex + 1)
    hasUnsavedChanges.value = true
    showToast(t('templateBuilder.toast.componentDuplicated'), 'success')
  }

  /**
   * Handle component update
   */
  function handleComponentUpdate(data) {
    const { sectionIndex, columnIndex, componentIndex, field, value } = data

    // Get the component to update
    const section = sections.value[sectionIndex]
    if (!section) return

    const column = section.columnsData[columnIndex]
    if (!column) return

    const component = column.components[componentIndex]
    if (!component) return

    // Update the specified field
    component[field] = value
    hasUnsavedChanges.value = true
  }

  return {
    addComponentToColumn,
    selectComponent,
    deleteComponent,
    duplicateComponent,
    handleComponentUpdate
  }
}
