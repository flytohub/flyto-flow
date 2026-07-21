/**
 * Parameter Schema Parser
 *
 * Parse params_schema and output_schema to UI field definitions.
 * Backend is single source of truth — labels/descriptions arrive pre-translated.
 *
 * Supports simple format (convention over configuration):
 *   - Array of strings → dropdown
 *   - String/Number/Boolean → auto-detect input type
 *   - Object with type → full schema
 */
import { detectFieldConfig } from './paramTypeDetection'
import { formatLabel } from '@/utils/format'

export { formatLabel }

/**
 * Normalize simple schema value to full schema object
 */
function normalizeSchema(value, key) {
  if (value && typeof value === 'object' && !Array.isArray(value) && value.type) return value
  if (Array.isArray(value) && value.length > 0 && typeof value[0] === 'string') {
    return { type: 'string', options: value.map(v => ({ value: v, label: v })), default: value[0] }
  }
  if (typeof value === 'boolean') return { type: 'boolean', default: value }
  if (typeof value === 'number') return { type: 'number', default: value }
  if (typeof value === 'string') return { type: 'string', default: value || '' }
  return value && typeof value === 'object' ? value : { type: 'string', default: '' }
}

function computeSmartStep(schema) {
  const min = schema.min ?? schema.minimum
  const max = schema.max ?? schema.maximum
  if (min !== undefined && max !== undefined) {
    const range = max - min
    if (range <= 1) return 0.01
    if (range <= 10) return 0.1
  }
  return 1
}

/**
 * Parse params_schema into form field definitions
 */
export function parseParamsSchema(paramsSchema, moduleId = '') {
  if (!paramsSchema) return []

  let schemaFields = paramsSchema
  let requiredFields = []

  if (paramsSchema.type === 'object' && paramsSchema.properties) {
    schemaFields = paramsSchema.properties
    requiredFields = paramsSchema.required || []
  }

  return Object.entries(schemaFields).map(([key, rawSchema]) => {
    const schema = normalizeSchema(rawSchema, key)
    const fieldConfig = detectFieldConfig(schema)
    const options = processOptions(schema)
    const visibility = (schema.ui_visibility || schema.visibility || '').toLowerCase()

    return {
      key,
      label: schema.label || schema.ui_label || formatLabel(key),
      description: schema.description || schema.ui_description || '',
      type: schema.type || 'string',
      componentType: fieldConfig.component,
      required: schema.required || requiredFields.includes(key),
      default: schema.default,
      placeholder: schema.placeholder || '',
      options,
      accept: schema.accept,
      min: schema.min ?? schema.minimum,
      max: schema.max ?? schema.maximum,
      step: schema.step ?? computeSmartStep(schema),
      format: schema.format,
      pathMode: schema.pathMode,
      widget: schema.widget || schema.ui?.widget,
      ui: schema.ui || null,
      enum: schema.enum,
      items: schema.items,
      minItems: schema.minItems,
      maxItems: schema.maxItems,
      properties: schema.properties,
      hidden: schema.hidden === true || visibility === 'hidden',
      expert: visibility === 'expert' || schema.advanced === true,
      group: schema.group || schema.ui?.group || 'basic',
      displayOptions: schema.displayOptions || null,
      showWhen: schema.showWhen || schema.show_when || schema.ui?.show_when || null,
      showIf: schema.showIf || null,
      hideIf: schema.hideIf || null
    }
  })
}

function processOptions(schema) {
  if (schema.enum && Array.isArray(schema.enum)) {
    return schema.enum.map(v => ({ value: v, label: v }))
  }

  if (schema.options && Array.isArray(schema.options)) {
    return schema.options.map(opt => {
      if (typeof opt === 'object') {
        return { value: opt.value, label: opt.label || opt.value }
      }
      return { value: opt, label: opt }
    })
  }

  return []
}

/**
 * Parse output_schema into result widget definitions
 */
export function parseOutputSchema(outputSchema) {
  if (!outputSchema) return []

  return Object.entries(outputSchema).map(([key, schema]) => {
    const fieldConfig = detectFieldConfig(schema, 'output')
    return {
      key,
      label: schema.label || formatLabel(key),
      description: schema.description || '',
      type: schema.type || 'string',
      widgetType: fieldConfig.widget || fieldConfig.component,
      format: schema.format,
      primary: schema.primary === true || key === 'result' || key === 'output'
    }
  })
}
