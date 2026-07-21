/**
 * Tools API Module
 *
 * S-Grade: Re-export all tools API functionality.
 *
 * Split modules:
 * - apiOperations.js: HTTP requests to tools endpoints
 * - localStorage.js: Local storage fallback operations
 */

// API operations
export {
  getTools,
  getTool,
  createTool,
  updateTool,
  deleteTool,
  executeTool,
  duplicateTool,
  getToolCategories,
  searchTools,
  parseCurl
} from './apiOperations'

// Local storage (for advanced usage)
export {
  generateId,
  getToolsFromLocal,
  getToolFromLocal,
  saveToolToLocal,
  updateToolInLocal,
  deleteToolFromLocal,
  searchToolsLocal,
  getDefaultCategories
} from './localStorage'

// Aggregate API object
import {
  getTools,
  getTool,
  createTool,
  updateTool,
  deleteTool,
  executeTool,
  duplicateTool,
  getToolCategories,
  searchTools,
  parseCurl
} from './apiOperations'

export const toolsAPI = {
  getTools,
  getTool,
  createTool,
  updateTool,
  deleteTool,
  executeTool,
  duplicateTool,
  getToolCategories,
  searchTools,
  parseCurl
}

export default toolsAPI
