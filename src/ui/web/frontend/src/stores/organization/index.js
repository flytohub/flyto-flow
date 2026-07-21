/**
 * Organization Store Module
 *
 * S-Grade: Re-export all organization store functionality.
 *
 * Split modules:
 * - state.js: State refs and getters
 * - orgActions.js: Organization CRUD operations
 * - memberActions.js: Member management operations
 * - organizationStoreCore.js: Main store
 */

// Main store
export { useOrganizationStore } from './organizationStoreCore'

// State factory (for testing/composition)
export { createOrganizationState, createOrganizationGetters } from './state'

// Action factories (for testing/composition)
export { createOrgActions } from './orgActions'
export { createMemberActions, createUtilityActions } from './memberActions'
