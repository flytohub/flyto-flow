/**
 * Variable Store Core
 *
 * S-Grade: Main variable store using extracted API actions.
 * Manages environment variables for workflows.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createVariableApiActions } from './variableApiActions'

/** Default filters */
const DEFAULT_FILTERS = {
  scope: null,
  scopeId: null,
  environment: 'all'
}

/** Default scope groups */
const DEFAULT_SCOPE_GROUPS = {
  workspace: [],
  project: [],
  workflow: []
}

/** Default environment groups */
const DEFAULT_ENV_GROUPS = {
  all: [],
  development: [],
  staging: [],
  production: []
}

export const useVariableStore = defineStore('variables', () => {
  // ========== State ==========
  const variables = ref([])
  const currentVariable = ref(null)
  const resolvedVariables = ref({})
  const filters = ref({ ...DEFAULT_FILTERS })
  const isLoading = ref(false)
  const error = ref(null)

  // Backend-computed groups
  const variablesByScope = ref({ ...DEFAULT_SCOPE_GROUPS })
  const variablesByEnvironment = ref({ ...DEFAULT_ENV_GROUPS })

  // ========== Getters ==========
  const hasVariables = computed(() => variables.value.length > 0)

  // ========== State refs for actions ==========
  const state = {
    variables, currentVariable, resolvedVariables, filters,
    isLoading, error, variablesByScope, variablesByEnvironment
  }

  // ========== API Actions ==========
  const {
    fetchVariables, fetchVariable, createVariable,
    updateVariable, deleteVariable, resolveVariables
  } = createVariableApiActions(state)

  // ========== Utility Actions ==========
  function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
  }

  function clearCurrentVariable() {
    currentVariable.value = null
  }

  function clearError() {
    error.value = null
  }

  function reset() {
    variables.value = []
    currentVariable.value = null
    resolvedVariables.value = {}
    filters.value = { ...DEFAULT_FILTERS }
    variablesByScope.value = { ...DEFAULT_SCOPE_GROUPS }
    variablesByEnvironment.value = { ...DEFAULT_ENV_GROUPS }
    isLoading.value = false
    error.value = null
  }

  return {
    // State
    variables, currentVariable, resolvedVariables, filters, isLoading, error,
    // Getters
    hasVariables, variablesByScope, variablesByEnvironment,
    // Actions
    fetchVariables, fetchVariable, createVariable, updateVariable, deleteVariable,
    resolveVariables, setFilters, clearCurrentVariable, clearError, reset
  }
})
