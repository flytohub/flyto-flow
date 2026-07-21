/**
 * Marketplace Filters Composable
 *
 * S-Grade: Filter state and actions for marketplace.
 * Single responsibility: managing filter state.
 *
 * Filtering and sorting is handled SERVER-SIDE via API query parameters.
 * This composable manages filter state that is sent to the backend.
 * The core composable watches these refs and re-fetches when they change.
 *
 * The only client-side filtering remaining is instant search feedback
 * (searchInput vs debounced searchQuery).
 */
import { ref, computed, onUnmounted } from 'vue'
import { DEFAULTS } from '@/config/defaults'
import { trackMarketplace } from '@/utils/telemetryTracker'

/**
 * Create marketplace filters
 *
 * @param {Object} options
 * @param {Ref} options.templates - Templates ref (server-filtered results)
 * @param {Ref} options.categories - Categories ref (from backend)
 * @param {Ref} options.currentPage - Current page ref
 * @returns {Object} Filter state and methods
 */
export function useMarketplaceFilters({ templates, categories, currentPage }) {
  // State — these are watched by useMarketplaceCore to trigger server re-fetch
  const searchInput = ref('')
  const searchQuery = ref('')
  const isSearching = ref(false)
  const selectedCategory = ref('')
  const priceFilter = ref('all')
  const sortBy = ref('popular')

  // Debounce timer
  let searchTimeout = null

  /**
   * Handle debounced search input.
   * Updates searchQuery after debounce, which triggers server re-fetch
   * via the watcher in useMarketplaceCore.
   */
  function handleSearchInput(value) {
    searchInput.value = value
    isSearching.value = true
    if (searchTimeout) clearTimeout(searchTimeout)
    searchTimeout = setTimeout(() => {
      searchQuery.value = value
      isSearching.value = false
      currentPage.value = 1
    }, DEFAULTS.TIMING.DEBOUNCE_SEARCH)
  }

  // Cleanup on unmount
  onUnmounted(() => {
    if (searchTimeout) {
      clearTimeout(searchTimeout)
      searchTimeout = null
    }
  })

  /**
   * Filtered templates — passthrough from server-filtered results.
   *
   * All filtering (category, pricing, search, sort) is now handled
   * server-side. This computed simply returns the templates ref
   * so that pagination and the UI continue to work unchanged.
   */
  const filteredTemplates = computed(() => {
    return templates.value
  })

  /**
   * Trigger search
   */
  function performSearch() {
    currentPage.value = 1
    if (searchQuery.value) {
      trackMarketplace.search(
        searchQuery.value,
        filteredTemplates.value.length,
        { category: selectedCategory.value || 'all' }
      )
    }
  }

  /**
   * Select a category
   */
  function selectCategory(catId) {
    const previousCategory = selectedCategory.value
    selectedCategory.value = catId
    currentPage.value = 1

    if (previousCategory !== catId) {
      const cat = categories.value.find(c => c.id === catId)
      trackMarketplace.filter('category', cat?.slug || 'all')
    }
  }

  /**
   * Get category by slug
   */
  function getCategoryBySlug(slug) {
    return categories.value.find(c => c.slug === slug)
  }

  /**
   * Set price filter with tracking
   */
  function setPriceFilter(filter) {
    const previousFilter = priceFilter.value
    priceFilter.value = filter
    currentPage.value = 1

    if (previousFilter !== filter) {
      trackMarketplace.filter('price', filter)
    }
  }

  /**
   * Set sort order with tracking
   */
  function setSortBy(sort) {
    const previousSort = sortBy.value
    sortBy.value = sort

    if (previousSort !== sort) {
      trackMarketplace.sort(sort, 'asc')
    }
  }

  /**
   * Clear all filters
   */
  function clearFilters() {
    searchInput.value = ''
    searchQuery.value = ''
    selectedCategory.value = ''
    priceFilter.value = 'all'
    currentPage.value = 1
  }

  return {
    // State
    searchInput,
    searchQuery,
    isSearching,
    selectedCategory,
    priceFilter,
    sortBy,

    // Computed
    filteredTemplates,

    // Methods
    handleSearchInput,
    performSearch,
    selectCategory,
    getCategoryBySlug,
    setPriceFilter,
    setSortBy,
    clearFilters
  }
}

export default useMarketplaceFilters
