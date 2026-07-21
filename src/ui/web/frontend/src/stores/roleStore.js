/**
 * Role Store
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All role logic split into role/* directory.
 *
 * Split modules:
 * - role/state.js: State refs and getters
 * - role/roleActions.js: Role CRUD operations
 * - role/permissionActions.js: Permission and assignment operations
 * - role/roleStoreCore.js: Main store
 */

// Re-export all from split modules
export {
  useRoleStore,
  createRoleState,
  createRoleGetters,
  createRoleActions,
  createPermissionActions,
  createUtilityActions
} from './role/index'
