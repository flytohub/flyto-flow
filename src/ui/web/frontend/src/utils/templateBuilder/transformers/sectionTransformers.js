/**
 * Section Transformers
 *
 * S-Grade: Section and component structure transformations.
 * Single responsibility: Flatten and rebuild section structures.
 */

/**
 * Convert section structure to flat component array
 * @param {Array<Object>} sections - Section array
 * @returns {Array<Object>} Flat component array
 */
export function flattenSectionsToComponents(sections) {
  if (!Array.isArray(sections)) {
    return []
  }

  const flatComponents = []

  sections.forEach(section => {
    if (!section.columnsData || !Array.isArray(section.columnsData)) {
      return
    }

    section.columnsData.forEach(column => {
      if (!column.components || !Array.isArray(column.components)) {
        return
      }

      column.components.forEach(component => {
        flatComponents.push(component)
      })
    })
  })

  return flatComponents
}

/**
 * Convert flat component array to section structure
 * @param {Array<Object>} components - Component array
 * @param {number} defaultColumns - Default column count (default: 1)
 * @returns {Array<Object>} Section array
 */
export function componentsToSections(components, defaultColumns = 1) {
  if (!Array.isArray(components) || components.length === 0) {
    return []
  }

  // Simple implementation: place all components in single section's single column
  const section = {
    id: 'section_1',
    columns: defaultColumns,
    grid: [12],
    gap: '16px',
    columnsData: [
      {
        components: [...components]
      }
    ]
  }

  return [section]
}
