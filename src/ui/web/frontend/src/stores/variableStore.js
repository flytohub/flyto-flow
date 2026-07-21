/**
 * Variable Store
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All functionality split into stores/variables/* directory.
 *
 * Split modules:
 * - variables/variableApiActions.js: API operations
 * - variables/variableStoreCore.js: Main store
 *
 * For credential management, use credentialStore.js instead.
 */

// Re-export store
export { useVariableStore } from './variables'

// Re-export action factory for advanced use
export { createVariableApiActions } from './variables'
