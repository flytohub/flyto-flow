/**
 * Audit Store Module
 *
 * S-Grade: Re-export all audit store functionality.
 *
 * Split modules:
 * - state.js: State refs and getters
 * - actions.js: Audit log operations
 * - auditStoreCore.js: Main store
 */

// Main store
export { useAuditStore } from './auditStoreCore'

// State factory (for testing/composition)
export { createAuditState, createAuditGetters } from './state'

// Action factories (for testing/composition)
export { createAuditActions, createUtilityActions } from './actions'
