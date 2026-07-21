/**
 * Composable for validating workflow before save
 * All validation is done via backend core API - frontend only handles display.
 */

import { workflowAPI } from '@/api/workflows'

/**
 * Validate workflow elements before saving
 * Calls backend core API for validation.
 * @param {Array} elements - VueFlow elements (nodes and edges)
 * @returns {Promise<{ ok: boolean, errors: Array, warnings: Array }>}
 */
export async function validateWorkflow(elements) {
  if (!elements || elements.length === 0) {
    return { ok: true, errors: [], warnings: [] }
  }

  const rawNodes = elements.filter(el => el.id && !el.source && !el.target)
  const rawEdges = elements.filter(el => el.source && el.target)

  if (rawNodes.length === 0) {
    return { ok: true, errors: [], warnings: [] }
  }

  // Transform VueFlow nodes to backend format
  // Backend expects: { id, module_id, params }
  // VueFlow nodes have: { id, data: { module, params } }
  const normalizeModuleId = (value) => {
    if (!value) return ''
    let moduleId = ''
    if (typeof value === 'string') {
      moduleId = value
    } else if (typeof value === 'object') {
      moduleId = value.moduleId || value.id || value.module || ''
    }
    // Normalize template module IDs:
    // template.invoke:xxx -> template.invoke
    // template.xxx (where xxx is not 'invoke') -> template.invoke
    if (moduleId.startsWith('template.invoke:')) {
      return 'template.invoke'
    }
    if (moduleId.startsWith('template.') && moduleId !== 'template.invoke') {
      return 'template.invoke'
    }
    return moduleId
  }

  const nodes = rawNodes.map(node => {
    const rawModuleId = node.data?.module || node.data?.moduleId || node.module || node.moduleId || ''
    const moduleId = normalizeModuleId(rawModuleId) || 'unknown'
    let params = node.data?.params || node.params || {}

    // For template nodes, ensure template_id is in params
    // IMPORTANT: Do NOT override library_id - it may differ from template_id
    // for purchased/forked templates. Backend is source of truth.
    if (moduleId === 'template.invoke') {
      // Only extract template_id from rawModuleId as fallback if not in params
      if (!params.template_id && typeof rawModuleId === 'string') {
        let extractedId = null
        if (rawModuleId.startsWith('template.invoke:')) {
          extractedId = rawModuleId.replace('template.invoke:', '')
        } else if (rawModuleId.startsWith('template.') && rawModuleId !== 'template.invoke') {
          extractedId = rawModuleId.replace('template.', '')
        }
        if (extractedId) {
          // Only set template_id, preserve library_id if already set
          params = {
            ...params,
            template_id: extractedId,
            library_id: params.library_id || extractedId
          }
        }
      }
    }

    return {
      id: node.id,
      moduleId,
      params
    }
  })

  // Transform edges to backend format (pass-through handles/data for backend logic)
  const edges = rawEdges.map(edge => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    sourceHandle: edge.sourceHandle,
    targetHandle: edge.targetHandle,
    type: edge.data?.edgeType === 'resource' ? 'resource' : undefined,
    data: edge.data || undefined
  }))

  // Convert to backend format and call validation API
  try {
    const result = await workflowAPI.validate({ nodes, edges })
    return {
      ok: result.valid,
      errors: result.errors || [],
      warnings: result.warnings || []
    }
  } catch (e) {
    // If validation API fails, return warning but allow save (offline mode)
    return {
      ok: true,
      errors: [],
      warnings: [{ code: 'VALIDATION_UNAVAILABLE', message: `Validation unavailable: ${e.message}` }]
    }
  }
}
