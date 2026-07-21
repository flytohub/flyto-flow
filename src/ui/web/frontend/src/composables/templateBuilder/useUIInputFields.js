/**
 * UI Input Fields Composable
 *
 * S-Grade: Extracts form field definitions from UI sections for workflow parameter binding.
 * Single responsibility: Compute available input fields from template UI for variable selector.
 */

import { computed } from 'vue'

// Form types that should appear in Parameter Settings / Variable Selector
const FORM_TYPES = [
  'input', 'number', 'email', 'password', 'url', 'tel',
  'textarea', 'select', 'checkbox', 'radio', 'switch',
  'date', 'time', 'range', 'rating', 'file'
]

/**
 * Create UI input fields composable
 *
 * @param {Object} options
 * @param {Ref|ComputedRef} options.sections - Template UI sections (or templateData with ui.sections)
 * @returns {Object} Composable with uiInputFields computed
 */
export function useUIInputFields(options) {
  const { sections } = options

  /**
   * Extract form components from sections as input field definitions
   * Used by workflow nodes to bind parameters to UI form inputs
   */
  const uiInputFields = computed(() => {
    const fields = []

    // Handle both direct sections array and templateData object
    const sectionsList = Array.isArray(sections?.value)
      ? sections.value
      : sections?.value?.ui?.sections || []

    sectionsList.forEach(section => {
      section.columnsData?.forEach(col => {
        col.components?.forEach(comp => {
          // Support both old format (type only) and new format (module)
          const isFormComponent =
            comp.module?.startsWith('form.') ||
            FORM_TYPES.includes(comp.type)

          if (isFormComponent) {
            fields.push({
              variableName: comp.params?.variableName || comp.params?.variable_name || comp.id,
              label: comp.label || comp.params?.label || comp.params?.variableName || comp.params?.variable_name || comp.id,
              type: comp.module || `form.${comp.type}`
            })
          }
        })
      })
    })

    return fields
  })

  return {
    uiInputFields
  }
}
