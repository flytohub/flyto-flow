/**
 * Audit Store State
 *
 * S-Grade: State refs and getters.
 * Single responsibility: Audit state management.
 */

import { ref, computed } from 'vue'
import { DEFAULTS } from '@/config/defaults'

/**
 * Create audit store state
 * @returns {Object} State refs
 */
export function createAuditState() {
  const logs = ref([])
  const currentLog = ref(null)
  const verificationStatus = ref(null)
  const stats = ref(null)
  const pagination = ref({
    page: 1,
    limit: DEFAULTS.PAGINATION.AUDIT,
    total: 0,
    totalPages: 1
  })
  const filters = ref({
    userId: null,
    action: null,
    resourceType: null,
    startDate: null,
    endDate: null,
    search: ''
  })
  const isLoading = ref(false)
  const isVerifying = ref(false)
  const error = ref(null)

  return {
    logs,
    currentLog,
    verificationStatus,
    stats,
    pagination,
    filters,
    isLoading,
    isVerifying,
    error,
  }
}

/**
 * Create audit store getters
 * @param {Object} state - State refs
 * @returns {Object} Computed getters
 */
export function createAuditGetters(state) {
  const { logs, verificationStatus } = state

  const hasLogs = computed(() => logs.value.length > 0)
  const isVerified = computed(() => verificationStatus.value?.verified === true)
  const lastVerifiedAt = computed(() => verificationStatus.value?.verifiedAt)

  return {
    hasLogs,
    isVerified,
    lastVerifiedAt,
  }
}
