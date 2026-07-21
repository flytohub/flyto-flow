/**
 * Organization Store State
 *
 * S-Grade: State refs and getters.
 * Single responsibility: Organization state management.
 */

import { ref, computed } from 'vue'

/**
 * Create organization store state
 * @returns {Object} State refs
 */
export function createOrganizationState() {
  const organization = ref(null)
  const members = ref([])
  const pendingInvites = ref([])
  const isLoading = ref(false)
  const isLoadingMembers = ref(false)
  const error = ref(null)

  // S-Grade: Backend-computed counts
  const memberCount = ref(0)
  const adminCount = ref(0)

  return {
    organization,
    members,
    pendingInvites,
    isLoading,
    isLoadingMembers,
    error,
    memberCount,
    adminCount,
  }
}

/**
 * Create organization store getters
 * @param {Object} state - State refs
 * @returns {Object} Computed getters
 */
export function createOrganizationGetters(state) {
  const { organization } = state

  const hasOrganization = computed(() => organization.value !== null)

  return {
    hasOrganization,
  }
}
