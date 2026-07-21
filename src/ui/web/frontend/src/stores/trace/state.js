/**
 * Trace Store State
 *
 * S-Grade: State refs and getters.
 * Single responsibility: Trace state management.
 */

import { ref, computed } from 'vue'

/**
 * Create trace store state
 * @returns {Object} State refs
 */
export function createTraceState() {
  const traces = ref([])
  const currentTrace = ref(null)
  const spans = ref([])
  const selectedSpan = ref(null)
  const pagination = ref({
    page: 1,
    limit: 20,
    total: 0,
    totalPages: 1
  })
  const filters = ref({
    status: null,
    workflowId: null,
    startTime: null,
    endTime: null,
    query: ''
  })
  const isLoading = ref(false)
  const isLoadingTrace = ref(false)
  const error = ref(null)

  // S-Grade: Backend-computed values (no frontend computation)
  const spanTree = ref([])
  const timelineData = ref({ spans: [], minTime: 0, maxTime: 0, totalDuration: 0 })

  return {
    traces,
    currentTrace,
    spans,
    selectedSpan,
    pagination,
    filters,
    isLoading,
    isLoadingTrace,
    error,
    spanTree,
    timelineData,
  }
}

/**
 * Create trace store getters
 * @param {Object} state - State refs
 * @returns {Object} Computed getters
 */
export function createTraceGetters(state) {
  const { traces, currentTrace } = state

  const hasTraces = computed(() => traces.value.length > 0)
  const hasCurrentTrace = computed(() => currentTrace.value !== null)

  return {
    hasTraces,
    hasCurrentTrace,
  }
}
