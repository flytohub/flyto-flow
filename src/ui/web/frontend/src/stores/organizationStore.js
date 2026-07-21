/**
 * Organization Store
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All organization logic split into organization/* directory.
 *
 * Split modules:
 * - organization/state.js: State refs and getters
 * - organization/orgActions.js: Organization CRUD operations
 * - organization/memberActions.js: Member management operations
 * - organization/organizationStoreCore.js: Main store
 */

// Re-export all from split modules
export {
  useOrganizationStore,
  createOrganizationState,
  createOrganizationGetters,
  createOrgActions,
  createMemberActions,
  createUtilityActions
} from './organization/index'
