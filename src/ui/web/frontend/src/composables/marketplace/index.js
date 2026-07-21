/**
 * Marketplace - Split Modules Re-exports
 *
 * S-Grade: Centralized exports for marketplace functionality.
 * All modules follow SRP < 200 lines each.
 *
 * Split structure:
 * - useMarketplaceFilters.js: Filter state and actions (~170 lines)
 * - useMarketplacePagination.js: Pagination logic (~90 lines)
 * - useMarketplaceActions.js: Install/purchase actions (~105 lines)
 * - useMarketplaceCore.js: Main composable (~165 lines)
 */

// Main composable
export { useMarketplace, default } from './useMarketplaceCore'

// Split composables
export { useMarketplaceFilters } from './useMarketplaceFilters'
export { useMarketplacePagination } from './useMarketplacePagination'
export { useMarketplaceActions } from './useMarketplaceActions'
