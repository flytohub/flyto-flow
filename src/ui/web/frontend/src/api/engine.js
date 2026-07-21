/**
 * Engine API
 * Variable introspection and autocomplete for workflow editor
 *
 * Uses flyto-core Engine SDK through backend API.
 */

import { post } from './client'

/**
 * Introspect available variables for a node
 *
 * Returns VarCatalog with all variables accessible at the node position.
 * S-Grade: Can return pre-flattened and pre-grouped data from backend.
 *
 * @param {Object} workflow - Workflow definition with nodes and edges
 * @param {string} nodeId - Target node ID
 * @param {Object} options - Additional options
 * @param {string} options.mode - 'edit' or 'runtime'
 * @param {Object} options.contextSnapshot - Runtime context (for runtime mode)
 * @param {boolean} options.flatten - Return pre-flattened items from backend
 * @param {boolean} options.group - Return pre-grouped items from backend
 * @returns {Promise<Object>} VarCatalog with optional items/grouped
 */
export async function introspectVariables(workflow, nodeId, options = {}) {
  const { mode = 'edit', contextSnapshot = null, flatten = false, group = false } = options

  try {
    return await post('/engine/introspect', {
      workflow,
      nodeId,
      mode,
      contextSnapshot,
      flatten,
      group
    })
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Get autocomplete suggestions for an expression
 *
 * @param {Object} workflow - Workflow definition
 * @param {string} nodeId - Target node ID
 * @param {string} prefix - Current input prefix
 * @param {Object} options - Additional options
 * @param {number} options.limit - Maximum suggestions (default 20)
 * @param {Object} options.contextSnapshot - Runtime context
 * @returns {Promise<Object>} AutocompleteResult with items
 */
export async function getAutocomplete(workflow, nodeId, prefix = '', options = {}) {
  const { limit = 20, contextSnapshot = null } = options

  try {
    return await post('/engine/autocomplete', {
      workflow,
      nodeId,
      prefix,
      limit,
      contextSnapshot
    })
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message, items: [] }
  }
}

/**
 * Validate an expression
 *
 * @param {Object} workflow - Workflow definition
 * @param {string} nodeId - Target node ID
 * @param {string} expression - Expression to validate
 * @param {Object} options - Additional options
 * @param {string} options.expectedType - Expected result type
 * @param {Object} options.contextSnapshot - Runtime context
 * @returns {Promise<Object>} Validation result
 */
export async function validateExpression(workflow, nodeId, expression, options = {}) {
  const { expectedType = null, contextSnapshot = null } = options

  try {
    return await post('/engine/validate', {
      workflow,
      nodeId,
      expression,
      expectedType,
      contextSnapshot
    })
  } catch (err) {
    return { ok: false, valid: false, error: err.userMessage || err.message }
  }
}

// ---------------------------------------------------------------------------
// flattenCatalog helpers (extracted to reduce nesting)
// ---------------------------------------------------------------------------

/** Flatten port fields into items array */
function _flattenFields(fields, basePath, category, extras = {}) {
  const items = []
  if (!fields) return items
  for (const [fieldName, fieldInfo] of Object.entries(fields)) {
    const fieldPath = `${basePath}.${fieldName}`
    items.push({
      path: fieldPath,
      display: fieldPath,
      type: fieldInfo.type || 'any',
      category,
      description: fieldInfo.description || '',
      insertText: fieldPath,
      ...extras
    })
  }
  return items
}

/** Flatten catalog.inputs into items */
function _flattenInputs(inputs) {
  const items = []
  if (!inputs) return items
  for (const [portId, portInfo] of Object.entries(inputs)) {
    const basePath = portId === 'main' ? 'input' : `inputs.${portId}`
    items.push({
      path: basePath,
      display: basePath,
      type: portInfo.type || 'any',
      category: 'input',
      description: portInfo.description || `Input port: ${portId}`,
      insertText: basePath
    })
    items.push(..._flattenFields(portInfo.fields, basePath, 'input'))
  }
  return items
}

/** Flatten catalog.nodes into items */
function _flattenNodes(nodes) {
  const items = []
  if (!nodes) return items
  for (const [nodeId, nodeInfo] of Object.entries(nodes)) {
    const branchExtras = {
      isConditional: nodeInfo.isConditional || false,
      branchSource: nodeInfo.branchSource,
      branchPort: nodeInfo.branchPort
    }

    items.push({
      path: nodeId,
      display: nodeId,
      type: 'object',
      category: 'node',
      description: `Output from ${nodeInfo.nodeType}`,
      insertText: nodeId,
      ...branchExtras
    })

    if (nodeInfo.ports) {
      for (const [portId, portInfo] of Object.entries(nodeInfo.ports)) {
        const portPath = `${nodeId}.${portId}`
        items.push({
          path: portPath,
          display: portPath,
          type: portInfo.type || 'any',
          category: 'node',
          description: portInfo.description || `Port: ${portId}`,
          insertText: portPath,
          ...branchExtras
        })
        items.push(..._flattenFields(portInfo.fields, portPath, 'node', branchExtras))
      }
    }
  }
  return items
}

/** Flatten a simple key-value section (params, globals, env) */
function _flattenKeyValueSection(section, prefix, category, defaultType = 'any', labelFn = null) {
  const items = []
  if (!section) return items
  for (const [key, info] of Object.entries(section)) {
    const path = `${prefix}.${key}`
    items.push({
      path,
      display: path,
      type: info.type || defaultType,
      category,
      description: info.description || (labelFn ? labelFn(key) : `${category}: ${key}`),
      insertText: path
    })
  }
  return items
}

/**
 * Build flat list of variables from VarCatalog for UI
 *
 * S-Grade: Uses backend-computed items when available.
 * Falls back to local computation if backend didn't flatten.
 *
 * @param {Object} catalog - VarCatalog from introspectVariables
 * @returns {Array<Object>} Flat list of variables
 */
export function flattenCatalog(catalog) {
  // S-Grade: Use backend-computed items if available
  if (catalog.items && Array.isArray(catalog.items)) {
    return catalog.items
  }

  // Fallback: compute locally
  return [
    // Input shorthand
    {
      path: 'input',
      display: 'input',
      type: 'any',
      category: 'input',
      description: 'Main input (shorthand)',
      insertText: 'input'
    },
    ..._flattenInputs(catalog.inputs),
    ..._flattenNodes(catalog.nodes),
    ..._flattenKeyValueSection(catalog.params, 'params', 'param', 'any', k => `Parameter: ${k}`),
    ..._flattenKeyValueSection(catalog.globals, 'global', 'global', 'any', k => `Global: ${k}`),
    ..._flattenKeyValueSection(catalog.env, 'env', 'env', 'string', k => `Environment: ${k}`),
  ]
}

/**
 * Group variables by category for sidebar display
 *
 * S-Grade: Uses backend-computed groups when available.
 * Falls back to local computation if backend didn't group.
 *
 * @param {Array<Object>} items - Flat list from flattenCatalog, or catalog object with grouped
 * @param {Object} options - Grouping options
 * @param {boolean} options.separateConditional - Show conditional vars in separate group
 * @returns {Object} Variables grouped by category
 */
export function groupByCategory(items, options = {}) {
  // S-Grade: Check if items is actually a catalog with pre-grouped data
  if (items && items.grouped && typeof items.grouped === 'object') {
    return items.grouped
  }

  // Fallback: compute locally
  const { separateConditional = true } = options

  const groups = {
    input: { label: 'Input', icon: 'ArrowRight', items: [] },
    node: { label: 'Nodes', icon: 'Box', items: [] },
    conditional: { label: 'Conditional', icon: 'GitBranch', items: [] },
    param: { label: 'Parameters', icon: 'Settings', items: [] },
    global: { label: 'Globals', icon: 'Globe', items: [] },
    env: { label: 'Environment', icon: 'Terminal', items: [] }
  }

  for (const item of items) {
    let category = item.category || 'node'

    // Separate conditional variables if enabled
    if (separateConditional && item.isConditional && category === 'node') {
      category = 'conditional'
    }

    if (groups[category]) {
      groups[category].items.push(item)
    }
  }

  // Filter out empty groups
  return Object.fromEntries(
    Object.entries(groups).filter(([, group]) => group.items.length > 0)
  )
}

// Named export for consistency
export const engineAPI = {
  introspectVariables,
  getAutocomplete,
  validateExpression,
  flattenCatalog,
  groupByCategory
}

export default engineAPI
