/**
 * Tool Storage Composable
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All functionality split into composables/toolStorage/* directory.
 *
 * Split modules:
 * - toolStorage/state.js: Shared singleton state
 * - toolStorage/toolApiActions.js: API actions
 * - toolStorage/toolHelpers.js: Tool utilities
 * - toolStorage/useToolStorageCore.js: Main composable
 */

// Re-export main composable
export { useToolStorage, default } from './toolStorage'

// Re-export helpers for advanced use
export {
  createNewTool,
  getParamsSchema,
  updateCurrentTool,
  setCurrentTool,
  clearCurrentTool,
  getToolById,
  getToolsByCategory
} from './toolStorage'
