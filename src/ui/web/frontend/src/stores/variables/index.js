/**
 * Variables Store - Split Modules Re-exports
 *
 * S-Grade: Centralized exports for variables functionality.
 *
 * Split structure:
 * - variableApiActions.js: API operations (~190 lines)
 * - variableStoreCore.js: Main store (~95 lines)
 */

// Main store
export { useVariableStore } from './variableStoreCore'

// Actions factory for advanced use
export { createVariableApiActions } from './variableApiActions'
