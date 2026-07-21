/**
 * UI Inputs Collection
 *
 * S-Grade: Collect UI input values.
 * Single responsibility: Extract form values from template UI.
 */

// Form types that should appear in Parameter Settings
export const FORM_TYPES = [
  'input', 'number', 'email', 'password', 'url', 'tel',
  'textarea', 'select', 'checkbox', 'radio', 'switch',
  'date', 'time', 'range', 'rating', 'file'
]

/**
 * Collect UI input values from all form components
 * @param {Object} templateData - Template data ref
 * @returns {Object} Values keyed by variable name
 */
export function collectUIInputValues(templateData) {
  const values = {}
  const sections = templateData.value?.ui?.sections || []

  sections.forEach(section => {
    section.columnsData?.forEach(col => {
      col.components?.forEach(comp => {
        const isFormComponent = comp.module?.startsWith('form.') || FORM_TYPES.includes(comp.type)
        if (isFormComponent) {
          const varName = comp.params?.variableName || comp.params?.variable_name || comp.id
          // Get the value - prioritize default field, then params.default
          const value = comp.default !== undefined ? comp.default : (comp.params?.default ?? '')
          values[varName] = value

          // For select/radio: also store the label text as varName__label
          // so downstream nodes can choose to use value or display text
          if (comp.type === 'select' || comp.type === 'radio' || comp.module === 'form.input_select' || comp.module === 'form.input_radio') {
            const options = comp.options || comp.params?.options || []
            const selected = options.find(opt => {
              const optVal = typeof opt === 'string' ? opt : opt.value
              return optVal === value
            })
            if (selected) {
              values[varName + '__label'] = typeof selected === 'string' ? selected : (selected.label || selected.value || '')
            } else {
              values[varName + '__label'] = value
            }
          }
        }
      })
    })
  })

  return values
}
