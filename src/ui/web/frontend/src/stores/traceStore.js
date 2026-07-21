/**
 * Trace Store
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All trace logic split into trace/* directory.
 *
 * Split modules:
 * - trace/state.js: State refs and getters
 * - trace/actions.js: Trace operations
 * - trace/traceStoreCore.js: Main store
 */

// Re-export all from split modules
export {
  useTraceStore,
  createTraceState,
  createTraceGetters,
  createTraceActions,
  createUtilityActions
} from './trace/index'
