/**
 * Marketplace Composable
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All functionality split into composables/marketplace/* directory.
 *
 * Split modules:
 * - marketplace/useMarketplaceFilters.js: Filter state and actions
 * - marketplace/useMarketplacePagination.js: Pagination logic
 * - marketplace/useMarketplaceActions.js: Install/purchase actions
 * - marketplace/useMarketplaceCore.js: Main composable
 */

// Re-export everything from split modules
export {
  useMarketplace,
  useMarketplaceFilters,
  useMarketplacePagination,
  useMarketplaceActions
} from './marketplace'

// Default export
export { default } from './marketplace'
