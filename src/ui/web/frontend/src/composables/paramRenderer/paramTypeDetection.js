/**
 * Parameter Type Detection
 *
 * S-Grade: Determine UI component/widget types from schema.
 * Single responsibility: type detection.
 *
 * Uses object mapping (no if-else chains).
 */

/**
 * Format-based component overrides
 * When a specific format is detected, use this component.
 *
 * IMPORTANT: Input component names MUST match backend _detect_component_type()
 * in services/normalizers/base.py — SchemaField.vue expects these exact names.
 */
const FORMAT_COMPONENT_MAP = {
  // String formats — names match backend _detect_component_type()
  multiline: 'textarea',
  text: 'textarea',
  path: 'path',
  url: 'url',
  email: 'email',
  ['password']: 'password',
  color: 'color',
  date: 'date',
  datetime: 'datetime',
  code: 'textarea',
  json: 'jsonEditor',
  // Output formats (only used when mode='output')
  image: 'image-preview',
  html: 'html-viewer',
  markdown: 'markdown-viewer',
  audio: 'audio-player',
  video: 'video-player',
  percentage: 'progress-bar',
  currency: 'currency-display',
  bytes: 'file-size-display',
  gallery: 'image-gallery',
  list: 'list-view'
}

/**
 * Accept-based component overrides (for file type)
 */
const ACCEPT_COMPONENT_MAP = {
  image: 'imageUpload',
  audio: 'fileUpload',
  video: 'fileUpload'
}

/**
 * Base type to component mapping
 * Names match backend _detect_component_type() for SchemaField.vue compatibility.
 */
const TYPE_COMPONENT_MAP = {
  string: 'text',
  number: 'number',
  integer: 'number',
  boolean: 'boolean',
  array: 'array',
  object: 'keyValue',
  file: 'fileUpload',
  multiselect: 'multiselect'
}

/**
 * Base type to output widget mapping
 */
const TYPE_OUTPUT_WIDGET_MAP = {
  string: 'text-block',
  number: 'number-display',
  integer: 'number-display',
  boolean: 'status-badge',
  array: 'table-view',
  object: 'json-viewer',
  file: 'file-download'
}

/**
 * Special condition detectors (order matters - first match wins)
 * Each returns component name or null
 */
const SPECIAL_DETECTORS = [
  // Has options/enum → dropdown
  {
    detect: (schema) => hasOptions(schema),
    component: 'select'
  },
  // Object with properties → nested object editor
  {
    detect: (schema) => schema.type === 'object' && schema.properties && Object.keys(schema.properties).length > 0,
    component: 'nestedObject'
  },
  // Number with min/max → slider
  {
    detect: (schema) => schema.type === 'number' && schema.min !== undefined && schema.max !== undefined,
    component: 'slider'
  },
  // File with specific accept type
  {
    detect: (schema) => schema.type === 'file' && schema.accept,
    component: (schema) => {
      const acceptKey = Object.keys(ACCEPT_COMPONENT_MAP).find(key => schema.accept.includes(key))
      return acceptKey ? ACCEPT_COMPONENT_MAP[acceptKey] : 'fileUpload'
    }
  },
  // Format override
  {
    detect: (schema) => schema.format && FORMAT_COMPONENT_MAP[schema.format],
    component: (schema) => FORMAT_COMPONENT_MAP[schema.format]
  }
]

/**
 * Check if schema has options (enum or options array)
 */
function hasOptions(schema) {
  return (schema.enum && Array.isArray(schema.enum) && schema.enum.length > 0) ||
         (schema.options && Array.isArray(schema.options) && schema.options.length > 0)
}

/**
 * Detect field configuration from schema
 * @param {Object} schema - Parameter schema definition
 * @param {string} mode - 'input' or 'output'
 * @returns {Object} { component, widget }
 */
export function detectFieldConfig(schema, mode = 'input') {
  const defaultComponent = mode === 'output' ? 'json-viewer' : 'text'

  // No schema
  if (!schema) {
    return { component: defaultComponent, widget: defaultComponent }
  }

  // Backend is single source of truth — if componentType is already set, use it directly
  // See: services/normalizers/base.py → _detect_component_type()
  if (schema.componentType) {
    return { component: schema.componentType, widget: schema.componentType }
  }

  // Check special detectors first
  for (const detector of SPECIAL_DETECTORS) {
    if (detector.detect(schema)) {
      const component = typeof detector.component === 'function'
        ? detector.component(schema)
        : detector.component
      return { component, widget: component }
    }
  }

  // Use type-based mapping
  const typeMap = mode === 'output' ? TYPE_OUTPUT_WIDGET_MAP : TYPE_COMPONENT_MAP
  const component = typeMap[schema.type] || defaultComponent

  return { component, widget: component }
}

/**
 * Determine UI component type from param schema (legacy API)
 * @param {Object} paramSchema - Parameter schema definition
 * @returns {string} Component type identifier
 */
export function getParamComponentType(paramSchema) {
  return detectFieldConfig(paramSchema, 'input').component
}

/**
 * Determine result widget type from output schema (legacy API)
 * @param {Object} outputSchema - Output field schema
 * @param {*} value - Actual output value (for type detection)
 * @returns {string} Widget type identifier
 */
export function getOutputWidgetType(outputSchema, value = null) {
  // Auto-detect from value if no schema
  if (!outputSchema && value !== null) {
    return detectFromValue(value)
  }

  return detectFieldConfig(outputSchema, 'output').widget
}

/**
 * Value type to widget mapping for runtime detection
 */
const VALUE_TYPE_WIDGET_MAP = {
  string: (v) => {
    const isImage = v.startsWith('data:image') || /\.(png|jpg|jpeg|gif|webp)$/i.test(v)
    const isUrl = v.startsWith('http')
    return isImage ? 'image-preview' : isUrl ? 'link-button' : 'text-block'
  },
  number: () => 'number-display',
  boolean: () => 'status-badge',
  array: () => 'table-view',
  object: () => 'json-viewer'
}

/**
 * Detect widget type from actual value
 */
function detectFromValue(value) {
  const valueType = Array.isArray(value) ? 'array' : typeof value
  const detector = VALUE_TYPE_WIDGET_MAP[valueType]

  return detector ? detector(value) : 'json-viewer'
}
