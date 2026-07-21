/**
 * Save Data Preparation
 *
 * S-Grade: Prepare template data for saving.
 * Single responsibility: Transform state to save format.
 *
 * Note: Uses async conversion to ensure backend is single source of truth.
 * ConversionError will be thrown in cloud mode if backend is unavailable.
 */

import {
  elementsToBackendStepsAsync,
  extractRequiredPermissions,
  debugLogSteps,
  ConversionError,
  ConversionErrorCodes
} from '../../../utils/converter'

/**
 * Compute input schema from UI components
 * This schema is used when the template is invoked as a module
 * @param {Array} sections - UI sections
 * @returns {Object} Input schema in JSON Schema format
 */
function computeInputSchema(sections) {
  if (!sections || sections.length === 0) return null

  const properties = {}
  const required = []

  // Form component types that accept user input
  const INPUT_TYPES = [
    'input', 'number', 'email', 'password', 'url', 'tel',
    'textarea', 'select', 'checkbox', 'radio', 'switch',
    'date', 'time', 'range', 'rating', 'file'
  ]

  // Component type to JSON schema type mapping
  const TYPE_MAP = {
    'input': 'string',
    'textarea': 'string',
    'number': 'number',
    'email': 'string',
    'password': 'string',
    'url': 'string',
    'tel': 'string',
    'select': 'string',
    'checkbox': 'boolean',
    'radio': 'string',
    'switch': 'boolean',
    'date': 'string',
    'time': 'string',
    'range': 'number',
    'rating': 'number',
    'file': 'string'
  }

  sections.forEach(section => {
    if (!section.columnsData) return

    section.columnsData.forEach(column => {
      if (!column.components) return

      column.components.forEach(comp => {
        const compType = comp.type || ''
        const compModule = comp.module || ''
        const isFormInput = compModule.startsWith('form.') || INPUT_TYPES.includes(compType)

        if (!isFormInput) return

        // Get the variable name - this is the key used in params.ui.{key}
        // Support both camelCase (variableName) and snake_case (variable_name)
        const key = comp.params?.variableName || comp.params?.variable_name || comp.id
        if (!key) return

        // Build property schema
        const propSchema = {
          type: TYPE_MAP[compType] || 'string',
          label: comp.label || comp.params?.label || key,
          description: comp.description || comp.params?.description || ''
        }

        // Add default value if exists
        if (comp.default !== undefined && comp.default !== null) {
          propSchema.default = comp.default
        }
        if (comp.params?.default !== undefined && comp.params?.default !== null) {
          propSchema.default = comp.params.default
        }

        // Add placeholder
        if (comp.placeholder || comp.params?.placeholder) {
          propSchema.placeholder = comp.placeholder || comp.params?.placeholder
        }

        // Add select/radio options
        if ((compType === 'select' || compType === 'radio') && (comp.options || comp.params?.options)) {
          propSchema.options = comp.options || comp.params?.options
        }

        // Track required fields
        if (comp.required || comp.params?.required) {
          required.push(key)
          propSchema.required = true
        }

        properties[key] = propSchema
      })
    })
  })

  // Return null if no input fields found
  if (Object.keys(properties).length === 0) return null

  return {
    type: 'object',
    properties,
    required: required.length > 0 ? required : undefined
  }
}

/**
 * Prepare save data from current template state
 * @param {Object} options
 * @param {Ref} options.elements - Workflow elements
 * @param {Ref} options.sections - UI sections
 * @param {Ref} options.templateData - Template data computed
 * @param {Ref} options.templateVisibility - Template visibility
 * @param {Ref} options.templateListed - Template listed status
 * @returns {Promise<Object>} Save data
 * @throws {ConversionError} In cloud mode when backend conversion fails
 */
export async function prepareSaveData(options) {
  const { elements, sections, templateData, templateVisibility, templateListed, viewport, errorHandling, checkpoints } = options

  // Convert visual elements to backend step format using async converter
  // This ensures backend is single source of truth for format conversion
  const steps = await elementsToBackendStepsAsync(elements.value)
  debugLogSteps('Saving to backend', steps)

  // Extract required permissions from steps
  const requiredPermissions = extractRequiredPermissions(steps)

  // NOTE: ui.sections is the source of truth for UI layout
  // ui.components is a flattened version for backward compatibility only
  // When reading templates, prefer sections over components
  // ui.components is kept for backward compatibility with older templates
  const flatComponents = []
  if (sections.value && sections.value.length > 0) {
    sections.value.forEach(section => {
      if (section.columnsData) {
        section.columnsData.forEach(column => {
          if (column.components) {
            column.components.forEach(comp => {
              flatComponents.push(comp)
            })
          }
        })
      }
    })
  }

  // Compute input schema from UI components
  // This is used when the template is invoked as a module
  const inputSchema = computeInputSchema(sections.value)

  return {
    name: templateData.value.name,
    description: templateData.value.description || '',
    steps: steps,
    ui: {
      // DEPRECATED: Use sections instead. Kept for backward compatibility.
      components: flatComponents.map(comp => ({
        id: comp.id,
        type: comp.type,
        label: comp.label,
        description: comp.description,
        placeholder: comp.placeholder,
        required: comp.required || false,
        default: comp.default,
        options: comp.options || [],
        validation: comp.validation || {},
        showIf: comp.showIf || null,
        onChange: comp.onChange || null
      })),
      // Source of truth for UI layout
      sections: sections.value,
      // Canvas viewport state (zoom/pan position)
      viewport: viewport?.value || null,
    },
    // Input schema computed from UI components - used when template is invoked as a module
    input_schema: inputSchema,
    requiredPermissions,
    visibility: templateVisibility.value,
    listed: templateListed.value,
    // Error handling configuration
    error_workflow_id: errorHandling?.value?.errorWorkflowId || null,
    error_handling: errorHandling?.value || null,
    // Checkpoints (human-in-the-loop pause points)
    checkpoints: checkpoints?.value || [],
  }
}
