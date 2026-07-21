/**
 * Config Store Actions
 *
 * S-Grade: Store actions for configuration.
 * Single responsibility: Load, get, and reset config values.
 */

import { getAllConfig } from '@/api/platform'
import { DEFAULTS } from './defaults'

/**
 * Inject node design dimensions as CSS custom properties on :root.
 * e.g. --node-branch-width: 76px; --node-branch-height: 76px;
 */
function _injectNodeDesignCSSVars(design) {
  if (!design || typeof document === 'undefined') return
  const root = document.documentElement.style
  for (const [nodeType, conf] of Object.entries(design)) {
    const dims = conf.dimensions
    if (!dims) continue
    const slug = nodeType.replace(/_/g, '-')
    root.setProperty(`--node-${slug}-width`, `${dims.width}px`)
    root.setProperty(`--node-${slug}-height`, `${dims.height}px`)
  }
}

/**
 * Create config actions from state refs
 * @param {Object} state - State refs
 * @returns {Object} Action functions
 */
export function createConfigActions(state) {
  const {
    // Core
    timing,
    layout,
    theme,
    limits,
    shortcuts,
    // Module config
    llm,
    triggers,
    http,
    paramTypes,
    outputTypes,
    // Marketplace
    marketplace,
    subscription,
    // Workflow
    workflowTypes,
    formTypes,
    // Misc
    countries,
    quickStart,
    messaging,
    breakpoints,
    nodeDesign,
    // Loading
    isLoaded,
    isLoading,
    error,
  } = state

  /**
   * Config field mapping: state ref key -> DEFAULTS key
   * Used by both loadConfig and reset to avoid duplication.
   */
  const CONFIG_FIELDS = [
    'timing', 'layout', 'theme', 'limits', 'shortcuts',
    'llm', 'triggers', 'http', 'paramTypes', 'outputTypes',
    'marketplace', 'subscription',
    'workflowTypes', 'formTypes',
    'countries', 'quickStart', 'messaging', 'breakpoints', 'nodeDesign',
  ]

  /**
   * Apply config values from a source object (or DEFAULTS if no source)
   * @param {Object|null} source - Config object from backend, or null for defaults
   */
  function applyConfigValues(source) {
    for (const key of CONFIG_FIELDS) {
      state[key].value = (source ? source[key] : null) || DEFAULTS[key]
    }
  }

  /**
   * Load all configuration from backend
   */
  async function loadConfig(forceRefresh = false) {
    if (!forceRefresh && (isLoaded.value || isLoading.value)) return

    isLoading.value = true
    error.value = null

    try {
      const config = await getAllConfig({ forceRefresh })
      applyConfigValues(config)
      _injectNodeDesignCSSVars(nodeDesign.value)
      isLoaded.value = true
    } catch (err) {
      console.error('Failed to load config:', err)
      error.value = err.message || 'Failed to load configuration'
    } finally {
      isLoading.value = false
    }
  }

  // =============================================================================
  // Core Config Getters
  // =============================================================================

  /**
   * Get a specific timing value with fallback
   */
  function getTiming(category, key, fallback = 1000) {
    return timing.value[category]?.[key] ?? fallback
  }

  /**
   * Get a specific layout value with fallback
   */
  function getLayout(category, key, fallback = 0) {
    return layout.value[category]?.[key] ?? fallback
  }

  /**
   * Get a specific theme color with fallback
   */
  function getColor(category, key, fallback = '#3b82f6') {
    return theme.value[category]?.[key] ?? fallback
  }

  /**
   * Get a specific limit value with fallback
   */
  function getLimit(category, key, fallback) {
    return limits.value[category]?.[key] ?? fallback
  }

  /**
   * Get a specific shortcut with fallback
   */
  function getShortcut(category, key, fallback = '') {
    return shortcuts.value[category]?.[key] ?? fallback
  }

  // =============================================================================
  // LLM Config Helpers
  // =============================================================================

  /**
   * Get LLM providers list
   */
  function getLLMProviders() {
    return llm.value.providers || []
  }

  /**
   * Get models for a specific provider
   */
  function getLLMModels(providerId) {
    const provider = llm.value.providers?.find(p => p.id === providerId)
    return provider?.models || []
  }

  /**
   * Get LLM defaults
   */
  function getLLMDefaults() {
    return llm.value.defaults || DEFAULTS.llm.defaults
  }

  // =============================================================================
  // HTTP Config Helpers
  // =============================================================================

  /**
   * Get HTTP methods
   */
  function getHTTPMethods() {
    return http.value.methods || []
  }

  /**
   * Get HTTP auth types
   */
  function getHTTPAuthTypes() {
    return http.value.authTypes || []
  }

  /**
   * Get HTTP body types
   */
  function getHTTPBodyTypes() {
    return http.value.bodyTypes || []
  }

  // =============================================================================
  // Triggers Config Helpers
  // =============================================================================

  /**
   * Get trigger types
   */
  function getTriggerTypes() {
    return triggers.value.types || []
  }

  // =============================================================================
  // Marketplace Config Helpers
  // =============================================================================

  /**
   * Get marketplace categories
   */
  function getMarketplaceCategories() {
    return marketplace.value.categories || []
  }

  /**
   * Get currencies
   */
  function getCurrencies() {
    return marketplace.value.currencies || []
  }

  /**
   * Get visibility options
   */
  function getVisibilityOptions() {
    return marketplace.value.visibilityOptions || []
  }

  // =============================================================================
  // Workflow Types Helpers
  // =============================================================================

  /**
   * Get node types
   */
  function getNodeTypes() {
    return workflowTypes.value.nodeTypes || []
  }

  /**
   * Get edge types
   */
  function getEdgeTypes() {
    return workflowTypes.value.edgeTypes || []
  }

  // =============================================================================
  // Form Types Helpers
  // =============================================================================

  /**
   * Get form field types
   */
  function getFormFieldTypes() {
    return formTypes.value.formTypes || []
  }

  /**
   * Get input types
   */
  function getInputTypes() {
    return formTypes.value.inputTypes || []
  }

  /**
   * Get output types
   */
  function getOutputTypes() {
    return formTypes.value.outputTypes || []
  }

  /**
   * Get binding sources
   */
  function getBindingSources() {
    return formTypes.value.bindingSources || []
  }

  // =============================================================================
  // Misc Helpers
  // =============================================================================

  /**
   * Get supported countries
   */
  function getCountries() {
    return countries.value || []
  }

  /**
   * Get quick start modules
   */
  function getQuickStartModules() {
    return quickStart.value.modules || []
  }

  /**
   * Get messaging providers
   */
  function getMessagingProviders() {
    return messaging.value.providers || []
  }

  /**
   * Get breakpoint types
   */
  function getBreakpointTypes() {
    return breakpoints.value.types || []
  }

  /**
   * Get subscription plans
   */
  function getSubscriptionPlans() {
    return subscription.value.plans || []
  }

  /**
   * Get dimensions for a node type from backend SSOT
   */
  function getNodeDimensions(nodeType) {
    const defaultDims = { shape: 'rectangle', width: 240, height: 76 }
    const conf = nodeDesign.value?.[nodeType]
    return conf?.dimensions || defaultDims
  }

  // =============================================================================
  // Reset
  // =============================================================================

  /**
   * Reset to defaults
   */
  function reset() {
    applyConfigValues(null)
    isLoaded.value = false
    isLoading.value = false
    error.value = null
  }

  return {
    // Main actions
    loadConfig,
    reset,

    // Core config getters
    getTiming,
    getLayout,
    getColor,
    getLimit,
    getShortcut,

    // LLM helpers
    getLLMProviders,
    getLLMModels,
    getLLMDefaults,

    // HTTP helpers
    getHTTPMethods,
    getHTTPAuthTypes,
    getHTTPBodyTypes,

    // Triggers helpers
    getTriggerTypes,

    // Marketplace helpers
    getMarketplaceCategories,
    getCurrencies,
    getVisibilityOptions,

    // Workflow types helpers
    getNodeTypes,
    getEdgeTypes,

    // Form types helpers
    getFormFieldTypes,
    getInputTypes,
    getOutputTypes,
    getBindingSources,

    // Misc helpers
    getCountries,
    getQuickStartModules,
    getMessagingProviders,
    getBreakpointTypes,
    getSubscriptionPlans,

    // Node design helpers
    getNodeDimensions,
  }
}
