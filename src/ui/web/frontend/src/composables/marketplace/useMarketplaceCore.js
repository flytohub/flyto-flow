/**
 * Marketplace Core Composable
 *
 * S-Grade: Main marketplace with data loading.
 * Uses split modules for filters, pagination, actions.
 *
 * Filtering and sorting are handled server-side via API query parameters.
 * The filter composable triggers re-fetch when filters change.
 */
import { ref, computed, watch } from 'vue'
import { templatesAPI } from '@/api/templates'
import { DEFAULTS } from '@/config/defaults'
import { formatCompactNumber } from '@/utils/format'
import i18n from '@/i18n'
import { asNonNegativeInteger, asObject, asRecordArray } from '@/utils/dataBoundary'

// Import from split modules
import { useMarketplaceFilters } from './useMarketplaceFilters'
import { useMarketplacePagination } from './useMarketplacePagination'
import { useMarketplaceActions } from './useMarketplaceActions'

/**
 * Create marketplace composable
 * @param {Object} options
 * @param {Function} options.onSuccess - Success callback
 * @param {Function} options.onError - Error callback
 * @returns {Object} Marketplace state and methods
 */
export function useMarketplace(options = {}) {
  const { onSuccess, onError } = options

  // Core state
  const templates = ref([])
  const categories = ref([])
  const loading = ref(true)
  const viewMode = ref('grid')

  // Library state (fetched once, reused across filter changes)
  let _installedIds = new Set()
  let _categoriesLoaded = false

  // Stats
  const stats = ref({
    total: 0,
    authors: 0,
    downloads: 0
  })

  // Initialize pagination first (needs currentPage ref)
  const currentPage = ref(1)

  // Initialize filters with dependencies
  const filters = useMarketplaceFilters({
    templates,
    categories,
    currentPage
  })

  // Initialize pagination with filtered templates + shared currentPage ref
  const pagination = useMarketplacePagination({
    filteredTemplates: filters.filteredTemplates,
    currentPage
  })

  // Initialize actions
  const actions = useMarketplaceActions({ onSuccess, onError })

  /**
   * All categories including "All" option
   */
  const allCategories = computed(() => {
    return [
      { id: '', name: i18n.global.t('marketplace.all', 'All'), slug: 'all', templateCount: stats.value.total },
      ...categories.value
    ]
  })

  /**
   * Featured templates
   */
  const featuredTemplates = computed(() => {
    return templates.value.filter(t => t.isFeatured).slice(0, DEFAULTS.PAGINATION.FEATURED_LIMIT)
  })

  /**
   * Fetch templates with current filter/sort parameters (server-side).
   * Categories and library are only fetched on first load.
   */
  async function fetchTemplates() {
    loading.value = true
    try {
      // Resolve category: filters store the category ID, backend expects slug or ID
      let categoryParam = undefined
      if (filters.selectedCategory.value) {
        const cat = categories.value.find(c => c.id === filters.selectedCategory.value)
        categoryParam = cat?.slug || filters.selectedCategory.value
      }

      const searchParams = {
        search: filters.searchQuery.value || undefined,
        category: categoryParam,
        pricing: filters.priceFilter.value !== 'all' ? filters.priceFilter.value : undefined,
        sortBy: filters.sortBy.value || 'popular',
        pageSize: 200,
      }

      const templatesRes = await templatesAPI.searchTemplates(searchParams)

      templates.value = asRecordArray(templatesRes.templates).map(t => ({
        ...t,
        isInstalled: _installedIds.has(t.id)
      }))

      // Add category slug to templates
      templates.value = templates.value.map(t => {
        const cat = categories.value.find(c => c.id === t.category || c.slug === t.category)
        return { ...t, categorySlug: cat?.slug || t.category || 'other' }
      })

      // Update stats from server response
      stats.value = {
        total: asNonNegativeInteger(templatesRes.total, templates.value.length),
        authors: new Set(templates.value.map(t => t.creatorId)).size,
        downloads: templates.value.reduce((sum, t) => sum + (t.downloads || t.downloadCount || 0), 0)
      }
    } catch (err) {
      onError?.(err)
    } finally {
      loading.value = false
    }
  }

  /**
   * Initial load: fetch categories, library, and templates.
   * Subsequent filter changes only re-fetch templates.
   */
  async function loadData() {
    loading.value = true
    try {
      // Fetch categories and library in parallel (only on first load)
      if (!_categoriesLoaded) {
        const [categoriesRes, libraryRes] = await Promise.all([
          templatesAPI.getCategories(),
          templatesAPI.getLibrary().catch(() => ({ ok: false, items: [] }))
        ])

        const safeLibrary = asObject(libraryRes)
        _installedIds = new Set(
          asRecordArray(safeLibrary.ok ? safeLibrary.items : []).map(item => item.templateId || item.id)
        )

        categories.value = asRecordArray(asObject(categoriesRes).categories)
        _categoriesLoaded = true
      }

      // Fetch templates with current filters (server-side)
      await fetchTemplates()

      // Calculate template count per category from full unfiltered set
      // (only meaningful on initial load; kept for sidebar counts)
      if (categories.value.length > 0) {
        categories.value = categories.value.map(cat => {
          const count = templates.value.filter(t =>
            t.category === cat.id || t.category === cat.slug || t.categorySlug === cat.slug
          ).length
          return { ...cat, templateCount: count }
        })
      }
    } catch (err) {
      onError?.(err)
    } finally {
      loading.value = false
    }
  }

  // Watch filter changes and re-fetch from server.
  // searchQuery is handled by the debounced handleSearchInput in the filters composable.
  watch(
    [filters.selectedCategory, filters.priceFilter, filters.sortBy],
    () => {
      // Only re-fetch if categories are already loaded (initial load complete)
      if (_categoriesLoaded) {
        currentPage.value = 1
        fetchTemplates()
      }
    }
  )

  // Watch debounced search query — re-fetch from server
  watch(filters.searchQuery, () => {
    if (_categoriesLoaded) {
      currentPage.value = 1
      fetchTemplates()
    }
  })


  return {
    // Core state
    templates,
    categories,
    loading,
    viewMode,
    stats,

    // Computed
    allCategories,
    featuredTemplates,

    // From filters
    searchInput: filters.searchInput,
    searchQuery: filters.searchQuery,
    isSearching: filters.isSearching,
    selectedCategory: filters.selectedCategory,
    priceFilter: filters.priceFilter,
    sortBy: filters.sortBy,
    filteredTemplates: filters.filteredTemplates,
    handleSearchInput: filters.handleSearchInput,
    performSearch: filters.performSearch,
    selectCategory: filters.selectCategory,
    getCategoryBySlug: filters.getCategoryBySlug,
    setPriceFilter: filters.setPriceFilter,
    setSortBy: filters.setSortBy,
    clearFilters: filters.clearFilters,

    // From pagination
    currentPage,
    pageSize: pagination.pageSize,
    totalPages: pagination.totalPages,
    paginatedTemplates: pagination.paginatedTemplates,
    visiblePages: pagination.visiblePages,
    setPage: pagination.setPage,
    prevPage: pagination.prevPage,
    nextPage: pagination.nextPage,

    // From actions
    installingId: actions.installingId,
    installTemplate: actions.installTemplate,
    removeTemplate: actions.removeTemplate,
    confirmRemoveTemplate: actions.confirmRemoveTemplate,
    cancelRemoveTemplate: actions.cancelRemoveTemplate,
    purchaseTemplate: actions.purchaseTemplate,
    showRemoveDialog: actions.showRemoveDialog,
    removeTarget: actions.removeTarget,
    removeWarningKey: actions.removeWarningKey,

    // Utilities
    loadData,
    fetchTemplates,
    formatCompactNumber
  }
}

export default useMarketplace
