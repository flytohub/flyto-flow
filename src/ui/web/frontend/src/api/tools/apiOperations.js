/**
 * Tools API Operations
 *
 * S-Grade: API CRUD operations for user-created tools.
 * Single responsibility: HTTP requests to tools endpoints.
 */

import { get, post, put, del } from '../client'
import {
  getToolsFromLocal,
  getToolFromLocal,
  saveToolToLocal,
  updateToolInLocal,
  deleteToolFromLocal,
  searchToolsLocal,
  getDefaultCategories,
  generateId
} from './localStorage'
import i18n from '@/i18n'

/**
 * Get all tools for current user
 * @returns {Promise<Object>} Tools list
 */
export async function getTools() {
  try {
    return await get('/tools')
  } catch (error) {
    return getToolsFromLocal()
  }
}

/**
 * Get single tool by ID
 * @param {string} toolId - Tool ID
 * @returns {Promise<Object>} Tool data
 */
export async function getTool(toolId) {
  try {
    return await get(`/tools/${toolId}`)
  } catch (error) {
    return getToolFromLocal(toolId)
  }
}

/**
 * Create new tool
 * @param {Object} tool - Tool definition
 * @returns {Promise<Object>} Created tool
 */
export async function createTool(tool) {
  try {
    return await post('/tools', tool)
  } catch (error) {
    return saveToolToLocal(tool)
  }
}

/**
 * Update existing tool
 * @param {string} toolId - Tool ID
 * @param {Object} tool - Updated tool definition
 * @returns {Promise<Object>} Updated tool
 */
export async function updateTool(toolId, tool) {
  try {
    return await put(`/tools/${toolId}`, tool)
  } catch (error) {
    return updateToolInLocal(toolId, tool)
  }
}

/**
 * Delete tool
 * @param {string} toolId - Tool ID
 * @returns {Promise<Object>} Result
 */
export async function deleteTool(toolId) {
  try {
    return await del(`/tools/${toolId}`)
  } catch (error) {
    return deleteToolFromLocal(toolId)
  }
}

/**
 * Execute tool with inputs
 * @param {string} toolId - Tool ID
 * @param {Object} inputs - Input values
 * @returns {Promise<Object>} Execution result
 */
export async function executeTool(toolId, inputs) {
  return await post(`/tools/${toolId}/execute`, { inputs })
}

/**
 * Duplicate tool
 * @param {string} toolId - Tool ID
 * @param {string} newName - New tool name
 * @returns {Promise<Object>} New tool
 */
export async function duplicateTool(toolId, newName) {
  try {
    return await post(`/tools/${toolId}/duplicate`, { name: newName })
  } catch (error) {
    const original = await getToolFromLocal(toolId)
    if (!original || !original.ok) {
      throw new Error(i18n.global.t('error.toolNotFound'))
    }
    const duplicate = {
      ...original.tool,
      id: generateId(),
      meta: {
        ...original.tool.meta,
        name: newName || `${original.tool.meta.name} (Copy)`
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    return saveToolToLocal(duplicate)
  }
}

/**
 * Get tool categories
 * @returns {Promise<Array>} Categories
 */
export async function getToolCategories() {
  try {
    return await get('/tools/categories')
  } catch (error) {
    return getDefaultCategories()
  }
}

/**
 * Search tools
 * @param {string} query - Search query
 * @param {Object} filters - Filters
 * @returns {Promise<Object>} Search results
 */
export async function searchTools(query, filters = {}) {
  try {
    const params = new URLSearchParams({ q: query, ...filters })
    return await get(`/tools/search?${params}`)
  } catch (error) {
    return searchToolsLocal(query, filters)
  }
}

/**
 * Parse a curl command into HTTP request parameters
 *
 * Backend-first: This ensures consistent parsing and secure handling
 * of credentials. The backend processes the curl command and returns
 * structured HTTP parameters.
 *
 * @param {string} curlCommand - The curl command to parse
 * @returns {Promise<Object>} Parsed HTTP request parameters
 */
export async function parseCurl(curlCommand) {
  return await post('/tools/parse-curl', { curl_command: curlCommand })
}
