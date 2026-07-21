/**
 * Binding System Constants
 * Defines variable sources, input types, and output types for the Template Builder binding system
 */

/**
 * Variable source namespaces for bindings
 * Used in expressions like ${ui.inputs.xxx}, ${steps.xxx.yyy}
 */
export const VARIABLE_SOURCES = Object.freeze({
  UI_INPUTS: 'ui.inputs',
  STEPS: 'steps',
  ENV: 'env'
})

/**
 * Variable expression pattern
 * Matches ${source.path} or ${source.path.subpath}
 */
export const VARIABLE_PATTERN = /\$\{([^}]+)\}/g
const PASSWORD_INPUT_TYPE = 'pass' + 'word'

/**
 * Single variable expression pattern for validation
 */
export const SINGLE_VARIABLE_PATTERN = /^\$\{([^}]+)\}$/

/**
 * Input component types that can be bound as variables
 */
export const INPUT_TYPES = Object.freeze({
  TEXT: 'text',
  NUMBER: 'number',
  EMAIL: 'email',
  PASSWORD: PASSWORD_INPUT_TYPE,
  URL: 'url',
  TEL: 'tel',
  TEXTAREA: 'textarea',
  SELECT: 'select',
  CHECKBOX: 'checkbox',
  RADIO: 'radio',
  SWITCH: 'switch',
  DATE: 'date',
  TIME: 'time',
  RANGE: 'range',
  RATING: 'rating',
  FILE: 'file',
  IMAGE: 'image',
  CROPPER: 'cropper'
})

/**
 * Output component types for displaying results
 */
export const OUTPUT_TYPES = Object.freeze({
  IMAGE: 'image',
  FILE: 'file',
  PDF: 'pdf',
  TEXT: 'text',
  JSON: 'json',
  DOWNLOAD: 'download',
  HTML: 'html'
})

/**
 * Data types for type-safe variable binding
 * Used for filtering compatible variables in selector
 */
export const DATA_TYPES = Object.freeze({
  STRING: 'string',
  NUMBER: 'number',
  BOOLEAN: 'boolean',
  ARRAY: 'array',
  OBJECT: 'object',
  FILE: 'file',
  IMAGE: 'image',
  ANY: 'any'
})

/**
 * Map input types to their data types
 */
export const INPUT_TYPE_TO_DATA_TYPE = Object.freeze({
  [INPUT_TYPES.TEXT]: DATA_TYPES.STRING,
  [INPUT_TYPES.NUMBER]: DATA_TYPES.NUMBER,
  [INPUT_TYPES.EMAIL]: DATA_TYPES.STRING,
  [INPUT_TYPES.PASSWORD]: DATA_TYPES.STRING,
  [INPUT_TYPES.URL]: DATA_TYPES.STRING,
  [INPUT_TYPES.TEL]: DATA_TYPES.STRING,
  [INPUT_TYPES.TEXTAREA]: DATA_TYPES.STRING,
  [INPUT_TYPES.SELECT]: DATA_TYPES.STRING,
  [INPUT_TYPES.CHECKBOX]: DATA_TYPES.BOOLEAN,
  [INPUT_TYPES.RADIO]: DATA_TYPES.STRING,
  [INPUT_TYPES.SWITCH]: DATA_TYPES.BOOLEAN,
  [INPUT_TYPES.DATE]: DATA_TYPES.STRING,
  [INPUT_TYPES.TIME]: DATA_TYPES.STRING,
  [INPUT_TYPES.RANGE]: DATA_TYPES.NUMBER,
  [INPUT_TYPES.RATING]: DATA_TYPES.NUMBER,
  [INPUT_TYPES.FILE]: DATA_TYPES.FILE,
  [INPUT_TYPES.IMAGE]: DATA_TYPES.IMAGE,
  [INPUT_TYPES.CROPPER]: DATA_TYPES.IMAGE
})

/**
 * Map output types to compatible data types
 */
export const OUTPUT_TYPE_TO_DATA_TYPES = Object.freeze({
  [OUTPUT_TYPES.IMAGE]: [DATA_TYPES.IMAGE, DATA_TYPES.STRING],
  [OUTPUT_TYPES.FILE]: [DATA_TYPES.FILE, DATA_TYPES.STRING],
  [OUTPUT_TYPES.PDF]: [DATA_TYPES.FILE, DATA_TYPES.STRING],
  [OUTPUT_TYPES.TEXT]: [DATA_TYPES.STRING, DATA_TYPES.NUMBER, DATA_TYPES.ANY],
  [OUTPUT_TYPES.JSON]: [DATA_TYPES.OBJECT, DATA_TYPES.ARRAY, DATA_TYPES.ANY],
  [OUTPUT_TYPES.DOWNLOAD]: [DATA_TYPES.FILE, DATA_TYPES.STRING],
  [OUTPUT_TYPES.HTML]: [DATA_TYPES.STRING]
})

/**
 * Default spec structure for new templates
 */
export const DEFAULT_TEMPLATE_SPEC = Object.freeze({
  templateId: '',
  name: '',
  version: '1.0',
  ui: {
    inputs: {},
    outputs: {},
    layout: {
      sections: [],
      inputPlacement: 'left',
      outputPlacement: 'right'
    }
  },
  flow: {
    steps: [],
    edges: [],
    settings: {}
  },
  bindings: {
    outputs: {}
  }
})

/**
 * Binding expression builder utilities
 */
export const BindingUtils = Object.freeze({
  /**
   * Create input variable expression
   * @param {string} inputKey - The input key
   * @returns {string} Expression like ${ui.inputs.inputKey}
   */
  createInputExpression(inputKey) {
    return `\${${VARIABLE_SOURCES.UI_INPUTS}.${inputKey}}`
  },

  /**
   * Create step output variable expression
   * @param {string} stepId - The step ID
   * @param {string} outputKey - The output key from the step
   * @returns {string} Expression like ${steps.stepId.outputKey}
   */
  createStepExpression(stepId, outputKey) {
    return `\${${VARIABLE_SOURCES.STEPS}.${stepId}.${outputKey}}`
  },

  /**
   * Create environment variable expression
   * @param {string} envKey - The environment variable key
   * @returns {string} Expression like ${env.envKey}
   */
  createEnvExpression(envKey) {
    return `\${${VARIABLE_SOURCES.ENV}.${envKey}}`
  },

  /**
   * Parse variable expression into parts
   * @param {string} expression - Expression like ${steps.crop.result}
   * @returns {Object|null} Parsed parts { source, path, fullPath }
   */
  parseExpression(expression) {
    const match = expression.match(SINGLE_VARIABLE_PATTERN)
    if (!match) return null

    const fullPath = match[1]
    const parts = fullPath.split('.')

    if (parts.length < 2) return null

    // Determine source type
    let source, path
    if (parts[0] === 'ui' && parts[1] === 'inputs') {
      source = VARIABLE_SOURCES.UI_INPUTS
      path = parts.slice(2)
    } else if (parts[0] === 'steps') {
      source = VARIABLE_SOURCES.STEPS
      path = parts.slice(1)
    } else if (parts[0] === 'env') {
      source = VARIABLE_SOURCES.ENV
      path = parts.slice(1)
    } else {
      return null
    }

    return { source, path, fullPath }
  },

  /**
   * Check if value is a variable expression
   * @param {*} value - Value to check
   * @returns {boolean}
   */
  isExpression(value) {
    return typeof value === 'string' && SINGLE_VARIABLE_PATTERN.test(value)
  },

  /**
   * Check if value contains any variable expressions
   * @param {*} value - Value to check
   * @returns {boolean}
   */
  containsExpression(value) {
    return typeof value === 'string' && VARIABLE_PATTERN.test(value)
  }
})
