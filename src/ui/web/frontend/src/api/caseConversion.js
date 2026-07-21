/**
 * Case Conversion Utilities (snake_case <-> camelCase)
 *
 * Extracted from client.js for reuse and testability.
 */

/**
 * Convert camelCase string to snake_case
 * @param {string} str - camelCase string
 * @returns {string} snake_case string
 */
export function camelToSnake(str) {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)
}

/**
 * Convert snake_case string to camelCase
 * @param {string} str - snake_case string
 * @returns {string} camelCase string
 */
export function snakeToCamel(str) {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
}

/**
 * Recursively convert object keys from camelCase to snake_case
 * @param {any} obj - Object to convert
 * @returns {any} Converted object
 */
export function convertKeysToSnake(obj) {
  if (obj === null || obj === undefined) return obj
  if (Array.isArray(obj)) return obj.map(convertKeysToSnake)
  if (typeof obj !== 'object') return obj
  if (obj instanceof Date) return obj
  if (obj instanceof FormData) return obj  // Don't convert FormData

  return Object.keys(obj).reduce((acc, key) => {
    const snakeKey = camelToSnake(key)
    acc[snakeKey] = convertKeysToSnake(obj[key])
    return acc
  }, {})
}

/**
 * Check if a string looks like a dynamic ID (e.g., node_xxx, step_xxx, uuid, timestamp-based)
 * These should NOT be converted from snake_case to camelCase
 * @param {string} str
 * @returns {boolean}
 */
function looksLikeDynamicId(str) {
  if (typeof str !== 'string') return false

  // UUID format - definitely a dynamic ID
  if (/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(str)) {
    return true
  }

  // Contains timestamp (10+ digits after underscore)
  if (/_\d{10,}/.test(str)) {
    return true
  }

  // Node/step IDs: must have numbers or random-looking suffix
  // e.g., node_123, node_abc123_def, step_0, step_xyz789
  // But NOT: node_id, node_status, execution_id (these are field names)
  // Key insight: dynamic IDs contain numbers, field names typically don't
  if (/^(node|step)_/.test(str)) {
    const suffix = str.substring(str.indexOf('_') + 1)
    // Dynamic IDs contain numbers or have random-looking parts
    if (/\d/.test(suffix) || suffix.length > 20) {
      return true
    }
  }

  return false
}

/**
 * Check if an object's keys appear to be dynamic IDs
 * If most keys look like dynamic IDs, don't convert them
 * @param {Object} obj
 * @returns {boolean}
 */
function hasOnlyDynamicIdKeys(obj) {
  const keys = Object.keys(obj)
  if (keys.length === 0) return false
  // If ANY key looks like a dynamic ID, preserve all keys
  return keys.some(key => looksLikeDynamicId(key))
}

/**
 * Keys whose VALUES should NOT be converted (preserve snake_case)
 * - params: workflow step params must stay snake_case for Core modules
 * - node_states: keys are node IDs, not field names
 * - config: module configuration
 * - defaultParams/default_params: module default params must stay snake_case
 * - params_schema/paramsSchema: property keys must match step.params keys (snake_case);
 *   internal property definitions are already camelCase from the normalizer
 */
const PRESERVE_VALUE_KEYS = new Set([
  'params',
  'node_states',
  'nodeStates',
  // Execution node maps: keys are user-defined node IDs (e.g., 'health_check', 'goto_page')
  // which must NOT be converted (health_check → healthCheck breaks node ID lookup)
  'node_timings',
  'nodeTimings',
  'node_outputs',
  'nodeOutputs',
  'node_inputs',
  'nodeInputs',
  'config',
  'defaultParams',
  'default_params',
  'params_schema',
  'paramsSchema',
  // Module metadata: keys are module IDs (e.g., 'image.qrcode_generate')
  // which must NOT be converted (qrcode_generate → qrcodeGenerate breaks lookup)
  'modules_metadata',
  'modulesMetadata',
  // Feature quotas: keys are feature IDs (e.g., 'core.execution_record_full')
  // which must NOT be converted to camelCase
  'quotas',
  // Node design: keys are node type IDs (e.g., 'ai_agent', 'ai_sub')
  // which must NOT be converted (ai_agent → aiAgent breaks CSS var lookup)
  'node_design',
  'nodeDesign'
])

/**
 * Recursively convert object keys from snake_case to camelCase
 * Automatically detects and preserves dynamic ID keys (node_xxx, step_xxx, etc.)
 * Also preserves values of certain keys (params, node_states) in snake_case
 * @param {any} obj - Object to convert
 * @param {string} parentKey - The key that led to this value (for preserve check)
 * @returns {any} Converted object
 */
export function convertKeysToCamel(obj, parentKey = '') {
  if (obj === null || obj === undefined) return obj
  if (Array.isArray(obj)) return obj.map(item => convertKeysToCamel(item, parentKey))
  if (typeof obj !== 'object') return obj
  if (obj instanceof Date) return obj

  // If parent key is in preserve list, don't convert this object's keys
  if (PRESERVE_VALUE_KEYS.has(parentKey)) {
    return obj  // Return as-is, no conversion
  }

  // If this object's keys look like dynamic IDs, preserve them as-is
  // but still convert the values recursively
  if (hasOnlyDynamicIdKeys(obj)) {
    const result = {}
    for (const key of Object.keys(obj)) {
      result[key] = convertKeysToCamel(obj[key], key)
    }
    return result
  }

  return Object.keys(obj).reduce((acc, key) => {
    const camelKey = snakeToCamel(key)
    acc[camelKey] = convertKeysToCamel(obj[key], key)
    return acc
  }, {})
}
