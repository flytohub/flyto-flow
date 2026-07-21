/**
 * Marketplace Pagination Composable
 *
 * S-Grade: Pagination state and computed for marketplace.
 * Single responsibility: pagination logic.
 */
import { ref, computed } from 'vue'
import { DEFAULTS } from '@/config/defaults'

/**
 * Create marketplace pagination
 * @param {Object} options
 * @param {ComputedRef} options.filteredTemplates - Filtered templates computed
 * @param {Ref} [options.currentPage] - External current page ref (optional)
 * @returns {Object} Pagination state and methods
 */
export function useMarketplacePagination({ filteredTemplates, currentPage: externalPage }) {
  // State — use external ref if provided, otherwise create own
  const currentPage = externalPage || ref(1)
  const pageSize = DEFAULTS.PAGINATION.MARKETPLACE

  /**
   * Total pages for pagination
   */
  const totalPages = computed(() =>
    Math.ceil(filteredTemplates.value.length / pageSize)
  )

  /**
   * Current page templates
   */
  const paginatedTemplates = computed(() => {
    const start = (currentPage.value - 1) * pageSize
    return filteredTemplates.value.slice(start, start + pageSize)
  })

  /**
   * Visible page numbers for pagination UI
   */
  const visiblePages = computed(() => {
    const pages = []
    const total = totalPages.value
    const current = currentPage.value

    if (total <= 7) {
      for (let i = 1; i <= total; i++) pages.push(i)
    } else {
      pages.push(1)
      if (current > 3) pages.push('...')
      for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
        pages.push(i)
      }
      if (current < total - 2) pages.push('...')
      pages.push(total)
    }

    return pages
  })

  /**
   * Set page
   */
  function setPage(page) {
    currentPage.value = page
  }

  /**
   * Go to previous page
   */
  function prevPage() {
    if (currentPage.value > 1) {
      currentPage.value--
    }
  }

  /**
   * Go to next page
   */
  function nextPage() {
    if (currentPage.value < totalPages.value) {
      currentPage.value++
    }
  }

  return {
    // State
    currentPage,
    pageSize,

    // Computed
    totalPages,
    paginatedTemplates,
    visiblePages,

    // Methods
    setPage,
    prevPage,
    nextPage
  }
}

export default useMarketplacePagination
