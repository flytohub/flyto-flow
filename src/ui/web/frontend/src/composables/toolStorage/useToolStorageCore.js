/**
 * Tool Storage Core
 *
 * S-Grade: Main tool storage composable using extracted modules.
 * Manages tool persistence and state.
 */

import { isInitialized } from './state'
import { createReadonlyRefs, createToolComputeds } from './state'
import {
  loadTools, loadCategories, loadTool, saveTool,
  removeTool, copyTool, search
} from './toolApiActions'
import {
  createNewTool, getParamsSchema, updateCurrentTool,
  setCurrentTool, clearCurrentTool, getToolById, getToolsByCategory
} from './toolHelpers'

/**
 * Use Tool Storage
 * @returns {Object} Tool storage interface
 */
export function useToolStorage() {
  // Get readonly state refs
  const stateRefs = createReadonlyRefs()

  // Get computed properties
  const computeds = createToolComputeds()

  /**
   * Initialize tool storage
   */
  async function initialize() {
    if (isInitialized.value) return

    await Promise.all([
      loadTools(),
      loadCategories()
    ])
  }

  return {
    // State (readonly)
    ...stateRefs,

    // Computed
    ...computeds,

    // Actions
    initialize,
    loadTools,
    loadCategories,
    loadTool,
    saveTool,
    removeTool,
    copyTool,
    search,
    createNewTool,
    updateCurrentTool,
    setCurrentTool,
    clearCurrentTool,
    getToolById,
    getToolsByCategory,
    getParamsSchema
  }
}

export default useToolStorage
