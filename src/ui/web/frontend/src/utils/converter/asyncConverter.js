/**
 * Async Step Converter
 *
 * Backend is single source of truth for workflow format conversion.
 * No local fallback — if backend fails, throw error.
 */

import { workflowAPI } from '@/api/workflows'
import { separateElements, applyEdgeVisuals } from '@/composables/workflowEditor/workflowConstants'
import { extractRawModuleId } from './helpers'

/**
 * Custom error class for conversion failures
 */
export class ConversionError extends Error {
  constructor(message, code, details = {}) {
    super(message)
    this.name = 'ConversionError'
    this.code = code
    this.details = details
  }
}

/**
 * Error codes for conversion failures
 */
export const ConversionErrorCodes = {
  BACKEND_UNAVAILABLE: 'BACKEND_UNAVAILABLE',
  CONVERSION_FAILED: 'CONVERSION_FAILED',
  INVALID_RESPONSE: 'INVALID_RESPONSE'
}

/**
 * Convert VueFlow elements to backend steps (async)
 * Always uses backend API. Throws on failure.
 *
 * @param {Array} elements - VueFlow elements (nodes and edges)
 * @returns {Promise<Array>} Backend step format
 * @throws {ConversionError} When backend fails
 */
export async function elementsToBackendStepsAsync(elements) {
  const { nodes, edges } = separateElements(elements)

  if (!nodes || nodes.length === 0) {
    return []
  }

  try {
    const result = await workflowAPI.vueFlowToSteps({
      nodes: nodes.map(n => {
        const moduleId = extractRawModuleId(n.data?.module) || extractRawModuleId(n.data?.moduleId)
        return {
          id: n.id,
          type: n.type,
          position: n.position,
          label: n.label,
          data: {
            ...(n.data || {}),
            module: moduleId || n.data?.module
          }
        }
      }),
      edges: edges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle,
        type: e.type,
        data: e.data,
        label: e.label
      }))
    })

    if (!result.ok) {
      throw new ConversionError(
        'Workflow conversion failed. Please try again or contact support.',
        ConversionErrorCodes.CONVERSION_FAILED,
        { originalError: result.error }
      )
    }

    return result.steps
  } catch (err) {
    if (err instanceof ConversionError) {
      throw err
    }
    throw new ConversionError(
      'Unable to connect to server for workflow conversion. Please check your connection.',
      ConversionErrorCodes.BACKEND_UNAVAILABLE,
      { originalError: err.message }
    )
  }
}

/**
 * Convert backend steps to VueFlow elements (async)
 * Always uses backend API. Applies frontend styling after.
 *
 * @param {Array} steps - Backend step format
 * @param {Object} options - Options
 * @param {Function} options.getModuleById - Function to lookup module metadata
 * @param {Object} options.iconMap - Map of icon names to components
 * @returns {Promise<Object>} { nodes: Array, edges: Array }
 * @throws {ConversionError} When backend fails
 */
export async function backendStepsToElementsAsync(steps, options = {}) {
  if (!steps || !Array.isArray(steps) || steps.length === 0) {
    return { nodes: [], edges: [] }
  }

  const { getModuleById, iconMap } = options

  try {
    const result = await workflowAPI.stepsToVueFlow({ steps })

    if (!result.ok) {
      throw new ConversionError(
        'Failed to load workflow. Please try again or contact support.',
        ConversionErrorCodes.CONVERSION_FAILED,
        { originalError: result.error }
      )
    }

    // Apply frontend-specific styling to nodes
    const nodes = (result.nodes || []).map(node => {
      const moduleId = node.data?.module
      const moduleInfo = getModuleById ? getModuleById(moduleId) : null

      let iconComponent = null
      if (moduleInfo?.icon && iconMap) {
        iconComponent = iconMap[moduleInfo.icon]
      }

      return {
        ...node,
        data: {
          ...node.data,
          icon: iconComponent,
          color: moduleInfo?.color || node.data?.color
        }
      }
    })

    // Apply frontend-specific styling to edges (single source of truth)
    const edges = (result.edges || []).map(edge => applyEdgeVisuals(edge))

    return { nodes, edges }
  } catch (err) {
    if (err instanceof ConversionError) {
      throw err
    }
    throw new ConversionError(
      'Unable to connect to server. Please check your connection.',
      ConversionErrorCodes.BACKEND_UNAVAILABLE,
      { originalError: err.message }
    )
  }
}

