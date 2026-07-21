/**
 * Template Data Service
 *
 * Unified entry point for importing/exporting template and workflow data.
 * Handles JSON and YAML formats with proper validation and normalization.
 *
 * Use this service instead of directly parsing JSON/YAML in components!
 */

import yaml from 'js-yaml'
import { importWorkflowFromYaml } from '../composables/workflowEditor/useWorkflowImport'
import { isTemplateModule, getBaseModuleType } from '../utils/moduleIdUtils'

/**
 * Import result type
 * @typedef {Object} ImportResult
 * @property {boolean} success
 * @property {'json'|'yaml'|null} format - Detected format
 * @property {Object|null} data - Parsed data (for JSON template)
 * @property {Array} nodes - VueFlow nodes (for YAML workflow)
 * @property {Array} edges - VueFlow edges (for YAML workflow)
 * @property {Object|null} workflowMeta - Workflow metadata
 * @property {Object|null} _ui - UI metadata from _ui block (positions, builder sections)
 * @property {Array<string>} warnings
 * @property {Array<string>} errors
 */

/**
 * Detect content format (JSON or YAML)
 * @param {string} content
 * @returns {'json'|'yaml'|'unknown'}
 */
export function detectFormat(content) {
  const trimmed = content.trim()

  // Check if it starts with JSON markers
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    try {
      JSON.parse(trimmed)
      return 'json'
    } catch {
      // Not valid JSON, might be YAML
    }
  }

  // Try parsing as YAML
  try {
    const parsed = yaml.load(trimmed)
    if (parsed && typeof parsed === 'object') {
      // Check for YAML-specific workflow markers
      if (parsed.steps || parsed.workflow || parsed.name) {
        return 'yaml'
      }
      // Could be either, default to JSON-like object
      return 'json'
    }
  } catch {
    // Not valid YAML either
  }

  return 'unknown'
}

/**
 * Normalize module ID format
 * Backend is single source of truth - minimal normalization needed.
 *
 * @param {string} moduleId
 * @returns {string}
 */
export function normalizeModuleId(moduleId) {
  if (!moduleId) return moduleId
  // Most normalization is now handled by backend
  // Only handle legacy underscore format for backwards compatibility
  if (moduleId.includes('_') && !moduleId.includes('.')) {
    return moduleId.replace(/_/g, '.')
  }
  return moduleId
}

/**
 * Normalize workflow step to match module catalog format
 * Backend is single source of truth - minimal normalization needed.
 *
 * @param {Object} step
 * @param {Function} getModuleById
 * @returns {Object}
 */
function normalizeStep(step, getModuleById) {
  const normalized = { ...step }

  // Normalize module ID (minimal - backend handles most normalization)
  const originalModule = step.module
  normalized.module = normalizeModuleId(originalModule)

  // Template modules: params already contain template_id/library_id from backend
  // No frontend manipulation needed

  // Try to find module with normalized ID
  if (getModuleById) {
    let module = getModuleById(normalized.module)

    // If not found, try common variations
    if (!module) {
      const variations = [
        originalModule,
        `core.${normalized.module}`,
        normalized.module.replace('.', '_'),
      ]

      for (const variant of variations) {
        module = getModuleById(variant)
        if (module) {
          normalized.module = variant
          break
        }
      }
    }
  }

  // Normalize params (ensure consistent types)
  if (step.params) {
    // Debug: log params before and after normalization
    if (import.meta.env?.DEV && Array.isArray(step.params)) {
    }
    normalized.params = normalizeParams(step.params)
    if (import.meta.env?.DEV) {
    }
  }

  return normalized
}

/**
 * Normalize parameters
 *
 * Simplified version - backend handles type coercion now.
 * Frontend only ensures params is a valid object.
 *
 * @param {Object} params
 * @returns {Object}
 */
function normalizeParams(params) {
  // Defensive: if params is array, return empty object (corrupted data)
  if (Array.isArray(params)) {
    return {}
  }
  if (!params || typeof params !== 'object') {
    return {}
  }

  // Return params directly - backend is the source of truth for types
  // Type coercion is done in backend/services/helpers/params_helpers.py
  return { ...params }
}

/**
 * Import content from file or text
 * Unified entry point for all imports
 *
 * @param {string} content - Raw content to import
 * @param {Object} options
 * @param {Function} options.getModuleById - Function to lookup module by ID
 * @param {Object} options.modulesMetadata - All modules metadata for connection validation
 * @param {boolean} options.strictMode - Reject unknown modules (default: false)
 * @param {boolean} options.autoNormalize - Auto-normalize module IDs (default: true)
 * @returns {Promise<ImportResult>}
 */
export async function importTemplateData(content, options = {}) {
  const {
    getModuleById = null,
    modulesMetadata = null,
    strictMode = false,
    autoNormalize = true
  } = options

  const result = {
    success: false,
    format: null,
    data: null,
    nodes: [],
    edges: [],
    workflowMeta: null,
    checkpoints: [],
    _ui: null,
    warnings: [],
    errors: []
  }

  // Detect format
  const format = detectFormat(content)
  result.format = format

  if (format === 'unknown') {
    result.errors.push('Unable to detect format. Expected JSON or YAML.')
    return result
  }

  // Handle JSON format (template data)
  if (format === 'json') {
    try {
      const data = JSON.parse(content)
      result.data = data
      result.success = true

      // Extract template info if available
      if (data.templateId || data.templateName || data.template_id || data.template_name) {
        result.workflowMeta = {
          id: data.templateId || data.template_id,
          name: data.templateName || data.template_name
        }
      }
    } catch (e) {
      result.errors.push(`JSON parse error: ${e.message}`)
    }
    return result
  }

  // Handle YAML format (workflow)
  if (format === 'yaml') {
    // Parse once to extract _ui block before preprocessing
    let parsedRaw = null
    try {
      parsedRaw = yaml.load(content)
    } catch {
      // Will be caught by importWorkflowFromYaml below
    }

    // Pre-process content if auto-normalize is enabled
    let processedContent = content
    if (autoNormalize && getModuleById) {
      const preprocessed = preprocessYamlContent(content, getModuleById)
      processedContent = preprocessed.content
      // Add preprocessing warnings to result
      result.warnings.push(...preprocessed.warnings)
    }

    // Use existing import utility (async)
    const importResult = await importWorkflowFromYaml(processedContent, {
      getModuleById,
      modulesMetadata,
      strictMode
    })

    result.success = importResult.success
    result.nodes = importResult.nodes
    result.edges = importResult.edges
    result.workflowMeta = importResult.workflowMeta
    result.checkpoints = importResult.checkpoints || []
    result.warnings.push(...importResult.warnings)
    result.errors = importResult.errors

    // Extract _ui block (positions, builder sections) for flyto-cloud
    if (parsedRaw?._ui) {
      result._ui = parsedRaw._ui

      // Override node positions from _ui.positions
      // (backend convert_steps_to_vueflow always auto-layouts, so we restore here)
      const uiPositions = parsedRaw._ui.positions
      if (uiPositions && result.nodes?.length) {
        for (const node of result.nodes) {
          const pos = uiPositions[node.id]
          if (Array.isArray(pos) && pos.length >= 2) {
            node.position = { x: pos[0], y: pos[1] }
          }
        }
      }
    }

    // Also extract description if workflowMeta doesn't have it
    if (parsedRaw?.description && result.workflowMeta) {
      result.workflowMeta.description = result.workflowMeta.description || parsedRaw.description
    }

    return result
  }

  return result
}

/**
 * Preprocess YAML content to normalize module IDs
 * @param {string} content
 * @param {Function} getModuleById
 * @returns {{ content: string, warnings: string[] }}
 */
function preprocessYamlContent(content, getModuleById) {
  const warnings = []
  try {
    const parsed = yaml.load(content)

    if (parsed?.steps) {
      parsed.steps = parsed.steps.map(step => normalizeStep(step, getModuleById))
    }

    return {
      content: yaml.dump(parsed, { indent: 2, lineWidth: -1 }),
      warnings
    }
  } catch (e) {
    warnings.push(`YAML preprocessing failed: ${e.message}. Using original content.`)
    return { content, warnings }
  }
}

/**
 * Import from AI suggestion
 * Special handling for AI-generated workflow suggestions
 * Uses strict mode to reject invalid connections
 *
 * @param {Object} suggestion - AI suggestion object with yaml_content
 * @param {Object} options
 * @param {Function} options.getModuleById
 * @param {Object} options.modulesMetadata - All modules metadata for connection validation
 * @returns {Promise<ImportResult>}
 */
export async function importFromAISuggestion(suggestion, options = {}) {
  const { getModuleById = null, modulesMetadata = null } = options

  const result = {
    success: false,
    format: 'yaml',
    data: null,
    nodes: [],
    edges: [],
    workflowMeta: null,
    checkpoints: [],
    warnings: [],
    errors: []
  }

  if (!suggestion?.yamlContent) {
    result.errors.push('No YAML content in suggestion')
    return result
  }

  // Parse and validate with strict mode - reject invalid connections
  const importResult = await importTemplateData(suggestion.yamlContent, {
    getModuleById,
    modulesMetadata,
    strictMode: true,  // AI suggestions must pass validation
    autoNormalize: true
  })

  // Copy results
  result.success = importResult.success
  result.nodes = importResult.nodes
  result.edges = importResult.edges
  result.checkpoints = importResult.checkpoints || []
  result._ui = importResult._ui || null
  result.warnings = importResult.warnings
  result.errors = importResult.errors

  // Use suggestion metadata if available
  result.workflowMeta = {
    id: suggestion.id || importResult.workflowMeta?.id,
    name: suggestion.name || importResult.workflowMeta?.name,
    description: suggestion.description
  }

  return result
}

// Maximum file size for import (5MB)
const MAX_IMPORT_FILE_SIZE = 5 * 1024 * 1024

/**
 * Import from file
 * Handles file reading and format detection
 *
 * @param {File} file
 * @param {Object} options
 * @param {Function} options.getModuleById
 * @param {boolean} options.strictMode
 * @returns {Promise<ImportResult>}
 */
export async function importFromFile(file, options = {}) {
  const result = {
    success: false,
    format: null,
    data: null,
    nodes: [],
    edges: [],
    workflowMeta: null,
    warnings: [],
    errors: []
  }

  // File size validation
  if (file.size > MAX_IMPORT_FILE_SIZE) {
    result.errors.push(`File too large: ${(file.size / 1024 / 1024).toFixed(2)}MB exceeds maximum ${MAX_IMPORT_FILE_SIZE / 1024 / 1024}MB`)
    return result
  }

  // Empty file check
  if (file.size === 0) {
    result.errors.push('File is empty')
    return result
  }

  try {
    const content = await file.text()
    const fileName = file.name.toLowerCase()

    // Determine format by extension first, then by content
    let forceFormat = null
    if (fileName.endsWith('.json')) {
      forceFormat = 'json'
    } else if (fileName.endsWith('.yaml') || fileName.endsWith('.yml')) {
      forceFormat = 'yaml'
    }

    const importResult = await importTemplateData(content, {
      ...options,
      // Trust file extension over content detection
      format: forceFormat
    })

    return importResult
  } catch (e) {
    result.errors.push(`File read error: ${e.message}`)
    return result
  }
}

/**
 * Export template data to JSON
 * @param {Object} data
 * @param {Object} options
 * @param {boolean} options.pretty - Pretty print (default: true)
 * @returns {string}
 */
export function exportToJson(data, options = {}) {
  const { pretty = true } = options
  return JSON.stringify(data, null, pretty ? 2 : 0)
}

/**
 * Export workflow to YAML
 * @param {Object} workflow
 * @param {Object} options
 * @returns {string}
 */
export function exportToYaml(workflow, options = {}) {
  return yaml.dump(workflow, {
    indent: 2,
    lineWidth: -1,
    ...options
  })
}

/**
 * Validate imported data against module catalog
 * Quick validation without full import
 *
 * @param {string} content
 * @param {Function} getModuleById
 * @returns {{ valid: boolean, issues: string[] }}
 */
export function quickValidate(content, getModuleById) {
  const issues = []

  try {
    const parsed = yaml.load(content)

    if (!parsed) {
      issues.push('Empty content')
      return { valid: false, issues }
    }

    if (parsed.steps) {
      for (const step of parsed.steps) {
        if (!step.module) {
          issues.push(`Step "${step.id || 'unknown'}": Missing module`)
          continue
        }

        const normalizedId = step.module
        const module = getModuleById(normalizedId) || getModuleById(step.module)

        if (!module) {
          issues.push(`Unknown module: ${step.module}`)
        }
      }
    }
  } catch (e) {
    issues.push(`Parse error: ${e.message}`)
  }

  return {
    valid: issues.length === 0,
    issues
  }
}
