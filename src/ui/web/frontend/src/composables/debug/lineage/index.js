/**
 * Lineage Module - Split Exports
 *
 * S-Grade: Centralized exports for lineage composable.
 *
 * Split structure:
 * - state.js: State and computed creation (~150 lines)
 * - graphActions.js: Graph loading actions (~70 lines)
 * - focusActions.js: Focus and selection actions (~110 lines)
 * - itemLineageActions.js: Item-level lineage (~110 lines)
 * - useLineageCore.js: Main composable (~90 lines)
 */

// Main composable
export { useLineage, default } from './useLineageCore'

// State factories for advanced use
export { createLineageState, createLineageComputed, getEmptySwimlane } from './state'

// Action factories for composition
export { createGraphActions } from './graphActions'
export { createFocusActions } from './focusActions'
export { createItemLineageActions } from './itemLineageActions'
