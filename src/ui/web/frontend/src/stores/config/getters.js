/**
 * Config Store Getters
 *
 * S-Grade: Computed getters for configuration.
 * Single responsibility: Provide convenient shortcuts to config values.
 */

import { computed } from 'vue'

/**
 * Create config getters from state refs
 * @param {Object} state - State refs
 * @returns {Object} Computed getters
 */
export function createConfigGetters(state) {
  const {
    timing,
    layout,
    theme,
    limits,
    llm,
    triggers,
    http,
    marketplace,
    subscription,
    workflowTypes,
    formTypes,
  } = state

  // =============================================================================
  // Timing shortcuts
  // =============================================================================
  const pollingInterval = computed(() => timing.value.polling?.default ?? 2000)
  const executionPollingInterval = computed(() => timing.value.polling?.executionStatus ?? 1000)
  const notificationDuration = computed(() => timing.value.notifications?.successDuration ?? 3000)
  const debounceDelay = computed(() => timing.value.debounce?.search ?? 300)

  // =============================================================================
  // Layout shortcuts
  // =============================================================================
  const nodeSpacing = computed(() => ({
    horizontal: layout.value.workflow?.horizontalSpacing ?? 320,
    vertical: layout.value.workflow?.verticalSpacing ?? 150,
  }))
  const initialPosition = computed(() => ({
    x: layout.value.workflow?.initialX ?? 200,
    y: layout.value.workflow?.initialY ?? 100,
  }))

  // =============================================================================
  // Theme shortcuts
  // =============================================================================
  const statusColors = computed(() => theme.value.status || {})
  const chartColors = computed(() => theme.value.charts?.palette || [])

  // =============================================================================
  // Limits shortcuts
  // =============================================================================
  const maxFileSize = computed(() => limits.value.files?.maxSizeBytes ?? 10485760)
  const pageSize = computed(() => limits.value.pagination?.defaultPageSize ?? 20)

  // =============================================================================
  // LLM shortcuts
  // =============================================================================
  const llmProviders = computed(() => llm.value.providers || [])
  const defaultLLMProvider = computed(() => llm.value.defaults?.provider ?? 'openai')
  const defaultLLMModel = computed(() => llm.value.defaults?.model ?? 'gpt-4o')

  // =============================================================================
  // Triggers shortcuts
  // =============================================================================
  const triggerTypes = computed(() => triggers.value.types || [])
  const defaultTriggerType = computed(() => triggers.value.defaults?.triggerType ?? 'manual')

  // =============================================================================
  // HTTP shortcuts
  // =============================================================================
  const httpMethods = computed(() => http.value.methods || [])
  const httpAuthTypes = computed(() => http.value.authTypes || [])
  const httpBodyTypes = computed(() => http.value.bodyTypes || [])

  // =============================================================================
  // Marketplace shortcuts
  // =============================================================================
  const marketplaceCategories = computed(() => marketplace.value.categories || [])
  const currencies = computed(() => marketplace.value.currencies || [])
  const visibilityOptions = computed(() => marketplace.value.visibilityOptions || [])
  const mutabilityOptions = computed(() => marketplace.value.mutabilityOptions || [])
  const priceSuggestions = computed(() => marketplace.value.priceSuggestions || [])

  // =============================================================================
  // Subscription shortcuts
  // =============================================================================
  const subscriptionPlans = computed(() => subscription.value.plans || [])
  const subscriptionStatuses = computed(() => subscription.value.statuses || [])

  // =============================================================================
  // Workflow types shortcuts
  // =============================================================================
  const nodeTypes = computed(() => workflowTypes.value.nodeTypes || [])
  const edgeTypes = computed(() => workflowTypes.value.edgeTypes || [])
  const portTypes = computed(() => workflowTypes.value.portTypes || [])

  // =============================================================================
  // Form types shortcuts
  // =============================================================================
  const formFieldTypes = computed(() => formTypes.value.formTypes || [])
  const inputTypes = computed(() => formTypes.value.inputTypes || [])
  const outputTypesList = computed(() => formTypes.value.outputTypes || [])
  const bindingSources = computed(() => formTypes.value.bindingSources || [])

  return {
    // Timing
    pollingInterval,
    executionPollingInterval,
    notificationDuration,
    debounceDelay,

    // Layout
    nodeSpacing,
    initialPosition,

    // Theme
    statusColors,
    chartColors,

    // Limits
    maxFileSize,
    pageSize,

    // LLM
    llmProviders,
    defaultLLMProvider,
    defaultLLMModel,

    // Triggers
    triggerTypes,
    defaultTriggerType,

    // HTTP
    httpMethods,
    httpAuthTypes,
    httpBodyTypes,

    // Marketplace
    marketplaceCategories,
    currencies,
    visibilityOptions,
    mutabilityOptions,
    priceSuggestions,

    // Subscription
    subscriptionPlans,
    subscriptionStatuses,

    // Workflow types
    nodeTypes,
    edgeTypes,
    portTypes,

    // Form types
    formFieldTypes,
    inputTypes,
    outputTypesList,
    bindingSources,
  }
}
