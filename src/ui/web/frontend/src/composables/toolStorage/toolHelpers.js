/**
 * Tool Helpers
 *
 * S-Grade: Tool creation and schema utilities.
 * Single responsibility: Tool data manipulation.
 *
 * Note: All data uses camelCase for consistency.
 */

import { tools, currentTool } from './state'

/**
 * Create a new empty tool
 * @param {string} name - Tool name
 * @param {string} category - Tool category
 * @returns {Object} New tool object
 */
export function createNewTool(name = '', category = 'other') {
  const newTool = {
    id: null,
    version: 1,
    meta: {
      name: name || 'Untitled Tool',
      description: '',
      category,
      tags: [],
      icon: 'Box',
      paramsSchema: {},
      outputSchema: {}
    },
    inputs: {},
    flow: {
      steps: [],
      outputs: {}
    },
    ui: {
      layout: 'auto',
      sections: []
    },
    createdAt: null,
    updatedAt: null,
    _dirty: true
  }

  currentTool.value = newTool
  return newTool
}

/**
 * Convert tool.inputs to paramsSchema format
 * @param {Object} tool - Tool object
 * @returns {Object} Params schema
 */
export function getParamsSchema(tool) {
  if (tool?.meta?.paramsSchema && Object.keys(tool.meta.paramsSchema).length > 0) {
    return tool.meta.paramsSchema
  }

  const inputs = tool?.inputs || {}
  const schema = {}

  for (const [key, def] of Object.entries(inputs)) {
    schema[key] = {
      type: def.type || 'string',
      label: def.label || key,
      description: def.description || def.help || '',
      required: def.required || false,
      default: def.default,
      placeholder: def.placeholder,
      accept: def.accept,
      min: def.min,
      max: def.max,
      step: def.step,
      format: def.format,
      enum: def.enum || (def.options?.map(o => o.value || o) || undefined),
      options: def.options
    }
  }

  return schema
}

/**
 * Update the current tool with new values
 * @param {Object} updates - Updates to apply
 */
export function updateCurrentTool(updates) {
  if (!currentTool.value) return

  currentTool.value = {
    ...currentTool.value,
    ...updates,
    _dirty: true
  }
}

/**
 * Set the current tool
 * @param {Object} tool - Tool to set as current
 */
export function setCurrentTool(tool) {
  currentTool.value = tool
}

/**
 * Clear the current tool
 */
export function clearCurrentTool() {
  currentTool.value = null
}

/**
 * Get a tool by ID from the tools list
 * @param {string} toolId - Tool ID
 * @returns {Object|undefined} Tool or undefined
 */
export function getToolById(toolId) {
  return tools.value.find(t => t.id === toolId)
}

/**
 * Get tools by category
 * @param {string} category - Category name
 * @returns {Array} Tools in category
 */
export function getToolsByCategory(category) {
  return tools.value.filter(t => t.meta?.category === category)
}
