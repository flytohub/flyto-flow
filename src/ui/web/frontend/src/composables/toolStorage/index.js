/**
 * Tool Storage - Split Modules Re-exports
 *
 * S-Grade: Centralized exports for tool storage functionality.
 *
 * Split structure:
 * - state.js: Shared singleton state (~70 lines)
 * - toolApiActions.js: API actions (~180 lines)
 * - toolHelpers.js: Tool utilities (~115 lines)
 * - useToolStorageCore.js: Main composable (~65 lines)
 */

// Main composable
export { useToolStorage, default } from './useToolStorageCore'

// State for advanced use
export {
  tools, categories, isLoading, error, isInitialized, currentTool,
  createReadonlyRefs, createToolComputeds
} from './state'

// API actions
export {
  loadTools, loadCategories, loadTool, saveTool,
  removeTool, copyTool, search
} from './toolApiActions'

// Helpers
export {
  createNewTool, getParamsSchema, updateCurrentTool,
  setCurrentTool, clearCurrentTool, getToolById, getToolsByCategory
} from './toolHelpers'
