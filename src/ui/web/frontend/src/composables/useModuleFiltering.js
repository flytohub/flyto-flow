/**
 * Module Filtering Composable
 *
 * Provides filtering and grouping logic for module selector.
 * Extracted from ModuleSelector.vue for reusability and testability.
 *
 * SECURITY NOTE:
 * Module visibility/tier filtering is for UI DISPLAY ONLY.
 * Actual module access control is enforced server-side.
 *
 * Prefer using backend-provided visibility flags:
 * - module.metadata.isVisible - Server-computed visibility
 * - module.metadata.tier - Server-assigned tier
 * - /api/modules response filters based on user's license
 *
 * The filtering logic here provides UX hints; it does NOT prevent
 * access to modules. Backend validates module usage at execution time.
 */

import { ref, computed, watch } from 'vue'

/**
 * Group modules by category
 * @param {Array} modules - Array of modules
 * @returns {Array} Grouped categories
 */
export function groupModulesByCategory(modules) {
  const grouped = {}
  for (const mod of modules) {
    const catName = mod.category || mod.categoryName || 'other'
    if (!grouped[catName]) {
      grouped[catName] = {
        name: catName,
        label: catName.charAt(0).toUpperCase() + catName.slice(1),
        icon: mod.categoryIcon || mod.icon,
        modules: []
      }
    }
    grouped[catName].modules.push(mod)
  }
  return Object.values(grouped)
}

/**
 * Filter modules by search query
 * @param {Array} modules - Array of modules
 * @param {string} query - Search query
 * @returns {Array} Filtered modules
 */
export function filterModulesByQuery(modules, query) {
  if (!query) return modules

  const lowerQuery = query.toLowerCase()
  return modules.filter(mod =>
    mod.label?.toLowerCase().includes(lowerQuery) ||
    mod.description?.toLowerCase().includes(lowerQuery) ||
    mod.module?.toLowerCase().includes(lowerQuery) ||
    mod.moduleId?.toLowerCase().includes(lowerQuery) ||
    (mod.tags && mod.tags.some(tag => tag.toLowerCase().includes(lowerQuery)))
  )
}

/**
 * Create module filtering composable
 *
 * SECURITY NOTE:
 * This composable provides client-side filtering for UI display.
 * Backend enforces actual access control - see /api/modules endpoint.
 *
 * The visibility/tier checks below are UX hints only:
 * - 'default' visibility = shown in standard mode
 * - 'expert' visibility = shown in expert mode
 * - 'hidden' visibility = not shown but may still be usable
 *
 * @param {Object} options - Configuration
 * @param {Ref<Array>} options.defaultModules - Default modules ref (from backend tiered API)
 * @param {Ref<Array>} options.expertModules - Expert modules ref (from backend tiered API)
 * @returns {Object} Filtering utilities
 */
export function useModuleFiltering(options = {}) {
  const {
    defaultModules = ref([]),
    expertModules = ref([]),
  } = options

  const searchQuery = ref('')
  const selectedCategoryFilter = ref(null)
  const showExpertMode = ref(false)

  // Auto-enable expert mode when no default modules exist
  watch(
    () => [defaultModules.value, expertModules.value],
    ([defaultMods, expertMods]) => {
      if ((!defaultMods || defaultMods.length === 0) && expertMods && expertMods.length > 0) {
        showExpertMode.value = true
      }
    },
    { immediate: true }
  )

  /**
   * Group default modules by category
   *
   * Backend /api/modules/tiered returns pre-filtered default/expert lists.
   * No client-side filtering needed — just group for display.
   */
  const defaultModulesGrouped = computed(() => {
    return groupModulesByCategory(defaultModules.value || [])
  })

  /**
   * Group expert modules by category
   *
   * Backend provides the expert list. Just group for display.
   */
  const expertModulesGrouped = computed(() => {
    return groupModulesByCategory(expertModules.value || [])
  })

  // Filter categories helper
  function filterCategories(categories) {
    let filtered = categories

    // Apply category filter
    if (selectedCategoryFilter.value) {
      filtered = filtered.filter(cat => cat.name === selectedCategoryFilter.value)
    }

    return filtered
      .map(cat => {
        let modules = cat.modules

        // Apply search filter
        if (searchQuery.value) {
          modules = filterModulesByQuery(modules, searchQuery.value)
        }

        return { ...cat, modules }
      })
      .filter(cat => cat.modules.length > 0)
  }

  // Filtered default categories
  const filteredDefaultCategories = computed(() => filterCategories(defaultModulesGrouped.value))

  // Filtered expert categories
  const filteredExpertCategories = computed(() => filterCategories(expertModulesGrouped.value))

  // Counts
  const defaultModuleCount = computed(() => {
    return (filteredDefaultCategories.value ?? []).reduce((sum, cat) => sum + cat.modules.length, 0)
  })

  const expertModuleCount = computed(() => {
    return (expertModulesGrouped.value ?? []).reduce((sum, cat) => sum + cat.modules.length, 0)
  })

  // Visible categories for filter pills
  const visibleCategories = computed(() => {
    const categories = new Map()

    // Add default categories
    for (const cat of defaultModulesGrouped.value) {
      categories.set(cat.name, cat)
    }

    // Add expert categories if showing
    if (showExpertMode.value) {
      for (const cat of expertModulesGrouped.value) {
        if (!categories.has(cat.name)) {
          categories.set(cat.name, cat)
        }
      }
    }

    return Array.from(categories.values()).sort((a, b) => a.label.localeCompare(b.label))
  })

  // Reset filters
  function resetFilters() {
    searchQuery.value = ''
    selectedCategoryFilter.value = null
  }

  return {
    // State
    searchQuery,
    selectedCategoryFilter,
    showExpertMode,

    // Computed
    defaultModulesGrouped,
    expertModulesGrouped,
    filteredDefaultCategories,
    filteredExpertCategories,
    visibleCategories,

    // Counts
    defaultModuleCount,
    expertModuleCount,

    // Actions
    resetFilters
  }
}
