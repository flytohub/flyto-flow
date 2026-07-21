/**
 * Engine Variables Composable
 *
 * Provides reactive variable catalog from Engine SDK.
 * Used by workflow editor components for variable selection and autocomplete.
 */

import { ref, computed, watch, onMounted } from 'vue'
import {
  introspectVariables,
  getAutocomplete,
  validateExpression,
  flattenCatalog,
  groupByCategory
} from '@/api/engine'

/**
 * Use Engine Variables
 *
 * @param {Object} options
 * @param {Ref<Object>} options.workflow - Reactive workflow definition
 * @param {Ref<string>} options.nodeId - Reactive current node ID
 * @param {Object} options.contextSnapshot - Optional runtime context
 * @returns {Object} Variable catalog and helper functions
 */
export function useEngineVariables(options = {}) {
  const { workflow, nodeId, contextSnapshot = null } = options

  // State
  const loading = ref(false)
  const error = ref(null)
  const catalog = ref(null)
  const flatVariables = ref([])
  const groupedVariables = ref({})

  // Fetch catalog when workflow/nodeId changes
  async function fetchCatalog() {
    if (!workflow?.value || !nodeId?.value) {
      catalog.value = null
      flatVariables.value = []
      groupedVariables.value = {}
      return
    }

    loading.value = true
    error.value = null

    try {
      const result = await introspectVariables(
        workflow.value,
        nodeId.value,
        {
          mode: contextSnapshot ? 'runtime' : 'edit',
          contextSnapshot
        }
      )

      catalog.value = result
      flatVariables.value = flattenCatalog(result)
      groupedVariables.value = groupByCategory(flatVariables.value)
    } catch (e) {
      error.value = e.message || 'Failed to load variables'
      catalog.value = null
      flatVariables.value = []
      groupedVariables.value = {}
    } finally {
      loading.value = false
    }
  }

  // Watch for changes
  if (workflow && nodeId) {
    watch(
      [workflow, nodeId],
      () => fetchCatalog(),
      { immediate: true, deep: true }
    )
  }

  // Convert to legacy format for existing VariableSelector
  const availableVariables = computed(() => {
    const result = {
      inputs: [],
      steps: [],
      env: []
    }

    for (const item of flatVariables.value) {
      const variable = {
        path: item.path,
        label: item.display,
        expression: item.insertText,
        dataType: mapType(item.type),
        description: item.description
      }

      if (item.category === 'input' || item.category === 'param') {
        result.inputs.push(variable)
      } else if (item.category === 'node') {
        result.steps.push(variable)
      } else if (item.category === 'env' || item.category === 'global') {
        result.env.push(variable)
      } else {
        result.steps.push(variable)
      }
    }

    return result
  })

  return {
    // State
    loading,
    error,
    catalog,
    flatVariables,
    groupedVariables,
    availableVariables,

    // Methods
    fetchCatalog,
    refresh: fetchCatalog
  }
}

/**
 * Use Autocomplete
 *
 * Provides autocomplete suggestions for expression input.
 *
 * @param {Object} options
 * @param {Ref<Object>} options.workflow - Reactive workflow definition
 * @param {Ref<string>} options.nodeId - Reactive current node ID
 * @returns {Object} Autocomplete state and methods
 */
export function useAutocomplete(options = {}) {
  const { workflow, nodeId, contextSnapshot = null } = options

  const loading = ref(false)
  const suggestions = ref([])
  const prefix = ref('')

  async function suggest(inputPrefix, limit = 20) {
    if (!workflow?.value || !nodeId?.value) {
      suggestions.value = []
      return []
    }

    prefix.value = inputPrefix
    loading.value = true

    try {
      const result = await getAutocomplete(
        workflow.value,
        nodeId.value,
        inputPrefix,
        { limit, contextSnapshot }
      )

      suggestions.value = result.items || []
      return suggestions.value
    } catch (e) {
      suggestions.value = []
      return []
    } finally {
      loading.value = false
    }
  }

  function clear() {
    suggestions.value = []
    prefix.value = ''
  }

  return {
    loading,
    suggestions,
    prefix,
    suggest,
    clear
  }
}

/**
 * Use Expression Validation
 *
 * Validates expressions against the variable catalog.
 *
 * @param {Object} options
 * @param {Ref<Object>} options.workflow - Reactive workflow definition
 * @param {Ref<string>} options.nodeId - Reactive current node ID
 * @returns {Object} Validation state and methods
 */
export function useExpressionValidation(options = {}) {
  const { workflow, nodeId, contextSnapshot = null } = options

  const loading = ref(false)
  const result = ref(null)

  async function validate(expression, expectedType = null) {
    if (!workflow?.value || !nodeId?.value) {
      result.value = { valid: false, error: 'No workflow context' }
      return result.value
    }

    loading.value = true

    try {
      const validationResult = await validateExpression(
        workflow.value,
        nodeId.value,
        expression,
        { expectedType, contextSnapshot }
      )

      result.value = validationResult
      return validationResult
    } catch (e) {
      result.value = { valid: false, error: e.message }
      return result.value
    } finally {
      loading.value = false
    }
  }

  function clear() {
    result.value = null
  }

  return {
    loading,
    result,
    validate,
    clear
  }
}

// Type mapping helper
function mapType(engineType) {
  const typeMap = {
    'string': 'string',
    'number': 'number',
    'boolean': 'boolean',
    'object': 'object',
    'array': 'array',
    'any': 'any'
  }
  return typeMap[engineType] || 'any'
}

export default useEngineVariables
