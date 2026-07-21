/**
 * Subflow Tabs - Split Modules Re-exports
 *
 * S-Grade: Centralized exports for subflow tab functionality.
 *
 * Split structure:
 * - types.js: Type definitions and factories (~65 lines)
 * - breadcrumbUtils.js: Breadcrumb building (~60 lines)
 * - useTabHistory.js: History management (~80 lines)
 * - tabOperations.js: Tab CRUD operations (~110 lines)
 * - useSubflowTabsCore.js: Main composable (~145 lines)
 */

// Main composable
export { useSubflowTabs } from './useSubflowTabsCore'

// Type factories
export {
  createRootTab,
  createSubflowTab
} from './types'

// Utilities
export {
  buildBreadcrumbs,
  findParentFlowId
} from './breadcrumbUtils'

export { useTabHistory } from './useTabHistory'

export {
  findChildTabs,
  canCloseTab,
  createTabMutators
} from './tabOperations'
