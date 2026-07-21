/**
 * Component Default Config
 *
 * S-Grade: Default component configurations.
 * Single responsibility: Apply default config based on component type.
 */

/**
 * Get default component configuration based on type
 * @param {string} type - Component type
 * @param {Object} component - Base component object
 */
export function applyDefaultConfig(type, component) {
  switch (type) {
    case 'input':
      component.inputType = 'text'
      component.placeholder = ''
      component.default = ''
      break
    case 'number':
      component.inputType = 'number'
      component.placeholder = ''
      component.default = ''
      break
    case 'email':
      component.inputType = 'email'
      component.placeholder = ''
      component.default = ''
      break
    case 'password':
      component.inputType = 'password'
      component.placeholder = ''
      component.default = ''
      break
    case 'url':
      component.inputType = 'url'
      component.placeholder = ''
      component.default = ''
      break
    case 'tel':
      component.inputType = 'tel'
      component.placeholder = ''
      component.default = ''
      break
    case 'select':
      component.options = [
        { value: 'option1', label: 'Option 1' },
        { value: 'option2', label: 'Option 2' }
      ]
      component.default = ''
      break
    case 'textarea':
      component.rows = 4
      component.placeholder = ''
      component.default = ''
      break
    case 'checkbox':
      component.default = false
      break
    case 'radio':
      component.options = [
        { value: 'yes', label: 'Yes' },
        { value: 'no', label: 'No' }
      ]
      component.default = ''
      break
    case 'switch':
      component.default = false
      break
    case 'date':
      component.default = ''
      break
    case 'time':
      component.default = ''
      break
    case 'range':
      component.min = 0
      component.max = 100
      component.step = 1
      component.default = 50
      break
    case 'rating':
      component.max = 5
      component.default = 0
      break
    case 'file':
      component.accept = ''
      component.multiple = false
      break
    case 'heading':
      component.text = 'Heading'
      component.level = 2
      break
    case 'text':
      component.text = 'Text content'
      component.variant = 'body'
      break
    case 'divider':
      component.variant = 'solid'
      break
    case 'image':
      component.src = ''
      component.alt = ''
      break
    case 'button':
      component.text = 'Submit'
      component.buttonType = 'submit'
      component.variant = 'primary'
      break
  }
}

/**
 * Form input types that should be available in Parameter Settings
 */
export const FORM_TYPES = [
  'input', 'number', 'email', 'password', 'url', 'tel',
  'textarea', 'select', 'checkbox', 'radio', 'switch',
  'date', 'time', 'range', 'rating', 'file'
]

/**
 * Check if type is a form type
 * @param {string} type - Component type
 * @returns {boolean}
 */
export function isFormType(type) {
  return FORM_TYPES.includes(type)
}
