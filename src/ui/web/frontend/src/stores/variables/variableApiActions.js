/**
 * Variable API Actions
 *
 * S-Grade: Variable CRUD and resolve operations.
 * Single responsibility: API communication.
 */

import variablesAPI from '@/api/variables'
import i18n from '@/i18n'
import { telemetry } from '@/services/telemetry'

/**
 * Create variable API action handlers
 * @param {Object} state - State refs
 * @returns {Object} API action functions
 */
export function createVariableApiActions(state) {
  const {
    variables, currentVariable, resolvedVariables, filters,
    isLoading, error, variablesByScope, variablesByEnvironment
  } = state

  /**
   * Fetch variables list with groupings
   */
  async function fetchVariables(params = {}) {
    isLoading.value = true
    error.value = null

    try {
      const result = await variablesAPI.listVariables({
        scope: params.scope || filters.value.scope,
        scopeId: params.scopeId || filters.value.scopeId,
        environment: params.environment || filters.value.environment,
        groupBy: 'all'
      })

      if (result.ok) {
        variables.value = result.variables || []

        if (result.byScope) {
          variablesByScope.value = result.byScope
        }
        if (result.byEnvironment) {
          variablesByEnvironment.value = result.byEnvironment
        }
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchVariables')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get single variable
   */
  async function fetchVariable(id) {
    isLoading.value = true
    error.value = null

    try {
      const result = await variablesAPI.getVariable(id)

      if (result.ok) {
        currentVariable.value = result.variable
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchVariable')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create variable
   */
  async function createVariable(data) {
    isLoading.value = true
    error.value = null

    try {
      const result = await variablesAPI.createVariable(data)

      if (result.ok) {
        variables.value.push(result.variable)

        telemetry.track('variable.create', {
          scope: data.scope,
          environment: data.environment
        })
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToCreateVariable')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update variable
   */
  async function updateVariable(id, data) {
    isLoading.value = true
    error.value = null

    try {
      const result = await variablesAPI.updateVariable(id, data)

      if (result.ok) {
        const index = variables.value.findIndex(v => v.id === id)
        if (index !== -1) {
          variables.value[index] = result.variable
        }
        if (currentVariable.value?.id === id) {
          currentVariable.value = result.variable
        }

        telemetry.track('variable.update', { variable_id: id })
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToUpdateVariable')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete variable
   */
  async function deleteVariable(id) {
    isLoading.value = true
    error.value = null

    try {
      const result = await variablesAPI.deleteVariable(id)

      if (result.ok) {
        variables.value = variables.value.filter(v => v.id !== id)
        if (currentVariable.value?.id === id) {
          currentVariable.value = null
        }

        telemetry.track('variable.delete', { variable_id: id })
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToDeleteVariable')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Resolve variables for a workflow
   */
  async function resolveVariables(workflowId, environment = 'production') {
    isLoading.value = true
    error.value = null

    try {
      const result = await variablesAPI.resolveVariables(workflowId, environment)

      if (result.ok) {
        resolvedVariables.value = result.resolved || {}
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToResolveVariables')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  return {
    fetchVariables,
    fetchVariable,
    createVariable,
    updateVariable,
    deleteVariable,
    resolveVariables
  }
}
