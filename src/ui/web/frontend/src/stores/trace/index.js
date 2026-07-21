/**
 * Trace Store Module
 *
 * S-Grade: Re-export all trace store functionality.
 *
 * Split modules:
 * - state.js: State refs and getters
 * - actions.js: Trace operations
 * - traceStoreCore.js: Main store
 */

// Main store
export { useTraceStore } from './traceStoreCore'

// State factory (for testing/composition)
export { createTraceState, createTraceGetters } from './state'

// Action factories (for testing/composition)
export { createTraceActions, createUtilityActions } from './actions'
