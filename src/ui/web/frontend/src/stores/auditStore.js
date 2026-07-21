/**
 * Audit Store
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All audit logic split into audit/* directory.
 *
 * Split modules:
 * - audit/state.js: State refs and getters
 * - audit/actions.js: Audit log operations
 * - audit/auditStoreCore.js: Main store
 */

// Re-export all from split modules
export {
  useAuditStore,
  createAuditState,
  createAuditGetters,
  createAuditActions,
  createUtilityActions
} from './audit/index'
