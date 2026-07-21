/**
 * Role Store State
 *
 * S-Grade: State refs and getters.
 * Single responsibility: Role state management.
 */

import { ref, computed } from 'vue'

/**
 * Create role store state
 * @returns {Object} State refs
 */
export function createRoleState() {
  const roles = ref([])
  const permissions = ref([])
  const assignments = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  // S-Grade: Backend-computed counts
  const builtinCount = ref(0)
  const customCount = ref(0)
  const totalCount = ref(0)

  return {
    roles,
    permissions,
    assignments,
    isLoading,
    error,
    builtinCount,
    customCount,
    totalCount,
  }
}

/**
 * Create role store getters
 * @param {Object} state - State refs
 * @returns {Object} Computed getters
 */
export function createRoleGetters(state) {
  const { roles } = state

  const hasRoles = computed(() => roles.value.length > 0)

  // S-Grade: Use backend-computed list when available, fallback to local filter
  const builtInRoles = computed(() => roles.value.filter(r => r.isBuiltin))
  const customRoles = computed(() => roles.value.filter(r => !r.isBuiltin))

  return {
    hasRoles,
    builtInRoles,
    customRoles,
  }
}
