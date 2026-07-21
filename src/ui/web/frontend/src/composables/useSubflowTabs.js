/**
 * Subflow Tabs Composable
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All functionality split into composables/subflowTabs/* directory.
 *
 * Split modules:
 * - subflowTabs/types.js: Type definitions and factories
 * - subflowTabs/breadcrumbUtils.js: Breadcrumb building
 * - subflowTabs/useTabHistory.js: History management
 * - subflowTabs/useSubflowTabsCore.js: Main composable
 */

// Re-export main composable
export { useSubflowTabs } from './subflowTabs'

// Re-export utilities for advanced use
export {
  createRootTab,
  createSubflowTab,
  buildBreadcrumbs,
  findParentFlowId,
  useTabHistory
} from './subflowTabs'
