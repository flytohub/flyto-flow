/**
 * Workflow Import Utilities
 *
 * Validates YAML imports using backend core API.
 * Frontend only handles display - all validation goes through core.
 *
 * Note: Uses async conversion with ConversionError handling.
 */

import yaml from 'js-yaml'
import { workflowAPI } from '../../api/workflows'
import {
  backendStepsToElementsAsync,
  ConversionError,
  ConversionErrorCodes
} from '@/utils/converter'
import { iconMap } from '@/utils/iconMap'
import { getBaseModuleType } from '@/utils/moduleIdUtils'

/**
 * Import result type
 * @typedef {Object} ImportResult
 * @property {boolean} success
 * @property {Array} nodes
 * @property {Array} edges
 * @property {Object} workflowMeta
 * @property {Array<string>} checkpoints - Node IDs with checkpoints
 * @property {Array<string>} warnings
 * @property {Array<string>} errors
 */

/**
 * Validate and import workflow from YAML
 * All validation is done via backend core API - frontend only handles display.
 *
 * @param {string} yamlContent - YAML content to import
 * @param {Object} options
 * @param {Function} options.getModuleById - Function to lookup module by ID (for UI display only)
 * @param {boolean} options.strictMode - Reject invalid workflows entirely (default: false)
 * @returns {Promise<ImportResult>}
 */
export async function importWorkflowFromYaml(yamlContent, { getModuleById, strictMode = false } = {}) {
  const result = {
    success: false,
    nodes: [],
    edges: [],
    workflowMeta: null,
    checkpoints: [],
    warnings: [],
    errors: []
  }

  // Parse YAML (js-yaml handles all YAML features correctly)
  let workflow
  try {
    workflow = yaml.load(yamlContent)
  } catch (e) {
    result.errors.push(`YAML parse error: ${e.message}`)
    return result
  }

  // Basic structure check (must have steps)
  if (!workflow.steps || !Array.isArray(workflow.steps) || workflow.steps.length === 0) {
    result.errors.push('Workflow must have at least one step')
    return result
  }

  // Validate connection targets (branch/switch) exist
  const stepIds = new Set(workflow.steps.map((s, i) => s.id || String(i)))
  workflow.steps.forEach((step, index) => {
    if (step.connections) {
      Object.entries(step.connections).forEach(([key, target]) => {
        const targetId = Array.isArray(target) ? target[0] : target
        if (targetId && !stepIds.has(targetId) && !stepIds.has(String(targetId))) {
          const msg = `Step "${step.id || index}" connection "${key}" references non-existent target "${targetId}"`
          if (strictMode) {
            result.errors.push(msg)
          } else {
            result.warnings.push(msg)
          }
        }
      })
    }
  })

  // If strict mode and has errors, abort early
  if (strictMode && result.errors.length > 0) {
    return result
  }

  // Validate workflow connections via backend core API
  try {
    const hasEdges = Array.isArray(workflow.edges) && workflow.edges.length > 0
    const validationPayload = hasEdges
      ? {
          nodes: workflow.steps.map(step => ({
            id: step.id,
            moduleId: getBaseModuleType(step.module),  // Base type for validation
            params: step.params || {},  // Use params directly - backend handles template_id
            data: { moduleId: step.module }  // Preserve full ID for metadata lookup
          })),
          edges: workflow.edges.map(edge => ({
            id: edge.id,
            source: edge.source,
            target: edge.target,
            sourceHandle: edge.sourceHandle,
            targetHandle: edge.targetHandle,
            type: edge.type,
            data: edge.data
          }))
        }
      : { steps: workflow.steps }
    const validation = await workflowAPI.validate(validationPayload)
    if (!validation.valid) {
      for (const error of validation.errors || []) {
        result.errors.push(error.message || JSON.stringify(error))
      }
    }
    // Add warnings from backend
    for (const warning of validation.warnings || []) {
      result.warnings.push(warning.message || JSON.stringify(warning))
    }
  } catch (e) {
    result.errors.push(`Validation failed: ${e.message}`)
  }

  // Backend says invalid → block import
  if (result.errors.length > 0) {
    return result
  }

  // Convert to VueFlow elements (always via backend)
  try {
    const { nodes, edges } = await backendStepsToElementsAsync(workflow.steps, {
      getModuleById,
      iconMap
    })
    const workflowMeta = {
      id: workflow.id,
      name: workflow.name,
      version: workflow.version,
      description: workflow.description,
      params: workflow.params,
      output: workflow.output
    }
    const checkpoints = workflow.checkpoints || []
    result.nodes = nodes
    result.edges = edges
    result.workflowMeta = workflowMeta
    result.checkpoints = checkpoints
    result.success = true
  } catch (e) {
    // Handle ConversionError with specific messages
    if (e instanceof ConversionError) {
      const errorMsg = e.code === ConversionErrorCodes.BACKEND_UNAVAILABLE
        ? 'Unable to connect to server for workflow conversion. Please check your connection.'
        : `Workflow conversion failed: ${e.message}`
      result.errors.push(errorMsg)
    } else {
      result.errors.push(`Conversion error: ${e.message}`)
    }
  }

  return result
}

/**
 * Check if workflow has any validation issues
 * @param {Array} nodes
 * @returns {boolean}
 */
export function hasValidationWarnings(nodes) {
  return nodes.some(n => n.data?._validationWarning)
}

/**
 * Get all validation warnings from nodes
 * @param {Array} nodes
 * @returns {Array<string>}
 */
export function getValidationWarnings(nodes) {
  return nodes
    .filter(n => n.data?._validationWarning)
    .map(n => n.data._validationWarning)
}
