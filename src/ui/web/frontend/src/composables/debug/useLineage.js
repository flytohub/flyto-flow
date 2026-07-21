/**
 * useLineage Composable
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All lineage logic split into lineage/* directory.
 *
 * Split modules:
 * - lineage/state.js: State and computed creation
 * - lineage/graphActions.js: Graph loading actions
 * - lineage/focusActions.js: Focus and selection actions
 * - lineage/itemLineageActions.js: Item-level lineage
 * - lineage/useLineageCore.js: Main composable
 */

// Re-export from split modules
export { useLineage, default } from './lineage'

// Re-export utilities for advanced use
export {
  createLineageState,
  createLineageComputed,
  getEmptySwimlane,
  createGraphActions,
  createFocusActions,
  createItemLineageActions
} from './lineage'
