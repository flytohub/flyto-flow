/**
 * Tool API Actions
 *
 * S-Grade: API-related actions for tool storage.
 * Single responsibility: API communication.
 */

import {
  getTools,
  getTool,
  createTool,
  updateTool,
  deleteTool,
  duplicateTool,
  getToolCategories,
  searchTools
} from '@/api/tools'
import {
  tools, categories, isLoading, error, isInitialized, currentTool
} from './state'

/**
 * Load all tools from API
 */
export async function loadTools() {
  if (isLoading.value) return

  isLoading.value = true
  error.value = null

  try {
    const result = await getTools()
    if (result.ok) {
      tools.value = result.tools || []
      isInitialized.value = true
    } else {
      error.value = result.error || 'Failed to load tools'
    }
  } catch (e) {
    error.value = e.message || 'Failed to load tools'
  } finally {
    isLoading.value = false
  }
}

/**
 * Load tool categories from API
 */
export async function loadCategories() {
  try {
    const result = await getToolCategories()
    if (result.ok) {
      categories.value = result.categories || []
    }
  } catch (e) {
    // Silently fail for categories
  }
}

/**
 * Load a single tool by ID
 * @param {string} toolId - Tool ID
 * @returns {Promise<Object|null>} Tool or null
 */
export async function loadTool(toolId) {
  isLoading.value = true
  error.value = null

  try {
    const result = await getTool(toolId)
    if (result.ok && result.tool) {
      currentTool.value = result.tool
      return result.tool
    } else {
      error.value = result.error || 'Tool not found'
      return null
    }
  } catch (e) {
    error.value = e.message || 'Failed to load tool'
    return null
  } finally {
    isLoading.value = false
  }
}

/**
 * Save a tool (create or update)
 * @param {Object} tool - Tool data
 * @returns {Promise<Object|null>} Saved tool or null
 */
export async function saveTool(tool) {
  isLoading.value = true
  error.value = null

  try {
    let result
    if (tool.id && tools.value.some(t => t.id === tool.id)) {
      result = await updateTool(tool.id, tool)
    } else {
      result = await createTool(tool)
    }

    if (result.ok && result.tool) {
      const existingIndex = tools.value.findIndex(t => t.id === result.tool.id)
      if (existingIndex >= 0) {
        tools.value[existingIndex] = result.tool
      } else {
        tools.value.push(result.tool)
      }

      currentTool.value = result.tool
      delete currentTool.value._dirty

      return result.tool
    } else {
      error.value = result.error || 'Failed to save tool'
      return null
    }
  } catch (e) {
    error.value = e.message || 'Failed to save tool'
    return null
  } finally {
    isLoading.value = false
  }
}

/**
 * Delete a tool
 * @param {string} toolId - Tool ID
 * @returns {Promise<boolean>} Success status
 */
export async function removeTool(toolId) {
  isLoading.value = true
  error.value = null

  try {
    const result = await deleteTool(toolId)
    if (result.ok) {
      tools.value = tools.value.filter(t => t.id !== toolId)
      if (currentTool.value?.id === toolId) {
        currentTool.value = null
      }
      return true
    } else {
      error.value = result.error || 'Failed to delete tool'
      return false
    }
  } catch (e) {
    error.value = e.message || 'Failed to delete tool'
    return false
  } finally {
    isLoading.value = false
  }
}

/**
 * Duplicate a tool
 * @param {string} toolId - Tool ID
 * @param {string} newName - New tool name
 * @returns {Promise<Object|null>} New tool or null
 */
export async function copyTool(toolId, newName) {
  isLoading.value = true
  error.value = null

  try {
    const result = await duplicateTool(toolId, newName)
    if (result.ok && result.tool) {
      tools.value.push(result.tool)
      return result.tool
    } else {
      error.value = result.error || 'Failed to duplicate tool'
      return null
    }
  } catch (e) {
    error.value = e.message || 'Failed to duplicate tool'
    return null
  } finally {
    isLoading.value = false
  }
}

/**
 * Search tools
 * @param {string} query - Search query
 * @param {Object} filters - Search filters
 * @returns {Promise<Array>} Matching tools
 */
export async function search(query, filters = {}) {
  try {
    const result = await searchTools(query, filters)
    return result.ok ? result.tools : []
  } catch {
    return []
  }
}
