/**
 * Section Actions
 *
 * S-Grade: Section operations.
 * Single responsibility: Add, update, move, delete sections.
 */

/**
 * Create section actions
 * @param {Object} state - State refs
 * @returns {Object} Section action functions
 */
export function createSectionActions(state) {
  const { sections, hasUnsavedChanges, counters } = state

  function addSection(columns) {
    const equalRatio = Math.floor(12 / columns)
    const remainder = 12 % columns
    const grid = Array(columns).fill(equalRatio)
    for (let i = 0; i < remainder; i++) {
      grid[i]++
    }

    const newSection = {
      id: `section_${counters.section++}`,
      columns,
      grid,
      gap: '16px',
      columnsData: Array.from({ length: columns }, (_, i) => ({
        columnIndex: i,
        components: []
      }))
    }

    sections.value.push(newSection)
    hasUnsavedChanges.value = true
    return newSection
  }

  function updateSectionGrid(sectionIndex, gridValues) {
    if (sections.value[sectionIndex]) {
      sections.value[sectionIndex].grid = gridValues.map(v => parseInt(v))
      hasUnsavedChanges.value = true
    }
  }

  function moveSection(fromIndex, direction) {
    const toIndex = direction === 'up' ? fromIndex - 1 : fromIndex + 1
    if (toIndex < 0 || toIndex >= sections.value.length) return

    const temp = sections.value[fromIndex]
    sections.value[fromIndex] = sections.value[toIndex]
    sections.value[toIndex] = temp
    hasUnsavedChanges.value = true
    return toIndex
  }

  function deleteSection(index) {
    sections.value.splice(index, 1)
    hasUnsavedChanges.value = true
  }

  return {
    addSection,
    updateSectionGrid,
    moveSection,
    deleteSection,
  }
}

/**
 * Create component actions
 * @param {Object} state - State refs
 * @returns {Object} Component action functions
 */
export function createComponentActions(state) {
  const { sections, hasUnsavedChanges, counters } = state

  function addComponent(sectionIndex, columnIndex, componentData) {
    const section = sections.value[sectionIndex]
    if (!section) return null

    const column = section.columnsData[columnIndex]
    if (!column) return null

    const newComponent = {
      ...componentData,
      id: `${componentData.type}_${counters.component++}`
    }

    column.components.push(newComponent)
    hasUnsavedChanges.value = true
    return newComponent
  }

  function updateComponent(location, field, value) {
    const { sectionIndex, columnIndex, componentIndex } = location
    const component = sections.value[sectionIndex]
      ?.columnsData[columnIndex]
      ?.components[componentIndex]

    if (component) {
      component[field] = value
      hasUnsavedChanges.value = true
    }
  }

  function deleteComponent(location) {
    const { sectionIndex, columnIndex, componentIndex } = location
    const column = sections.value[sectionIndex]?.columnsData[columnIndex]

    if (column) {
      column.components.splice(componentIndex, 1)
      hasUnsavedChanges.value = true
      return true
    }
    return false
  }

  function duplicateComponent(location) {
    const { sectionIndex, columnIndex, componentIndex } = location
    const column = sections.value[sectionIndex]?.columnsData[columnIndex]
    const original = column?.components[componentIndex]

    if (!original) return null

    const newComponent = JSON.parse(JSON.stringify(original))
    newComponent.id = `${original.type}_${counters.component++}`
    newComponent.label = `${original.label} (Copy)`

    column.components.splice(componentIndex + 1, 0, newComponent)
    hasUnsavedChanges.value = true
    return newComponent
  }

  function getComponent(location) {
    if (!location) return null
    const { sectionIndex, columnIndex, componentIndex } = location
    return sections.value[sectionIndex]
      ?.columnsData[columnIndex]
      ?.components[componentIndex]
  }

  return {
    addComponent,
    updateComponent,
    deleteComponent,
    duplicateComponent,
    getComponent,
  }
}

/**
 * Create save actions
 * @param {Object} state - State refs
 * @returns {Object} Save action functions
 */
export function createSaveActions(state) {
  const { hasUnsavedChanges, isSaving, autoSaveEnabled } = state

  function markSaved() {
    hasUnsavedChanges.value = false
  }

  function setSaving(saving) {
    isSaving.value = saving
  }

  function setAutoSaveEnabled(enabled) {
    autoSaveEnabled.value = enabled
  }

  function toggleAutoSave() {
    autoSaveEnabled.value = !autoSaveEnabled.value
    return autoSaveEnabled.value
  }

  return {
    markSaved,
    setSaving,
    setAutoSaveEnabled,
    toggleAutoSave,
  }
}
