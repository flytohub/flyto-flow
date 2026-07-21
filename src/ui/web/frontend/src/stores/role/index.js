/**
 * Role Store Module
 *
 * S-Grade: Re-export all role store functionality.
 *
 * Split modules:
 * - state.js: State refs and getters
 * - roleActions.js: Role CRUD operations
 * - permissionActions.js: Permission and assignment operations
 * - roleStoreCore.js: Main store
 */

// Main store
export { useRoleStore } from './roleStoreCore'

// State factory (for testing/composition)
export { createRoleState, createRoleGetters } from './state'

// Action factories (for testing/composition)
export { createRoleActions } from './roleActions'
export { createPermissionActions, createUtilityActions } from './permissionActions'
