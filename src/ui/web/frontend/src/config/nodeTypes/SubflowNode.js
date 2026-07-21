/**
 * Subflow Node - External Workflow Reference
 *
 * Execution modes:
 * - inline: Blocking execution, waits for subflow completion
 * - spawn: Creates new execution, returns execution ID
 * - async: Fire and forget, continues immediately
 *
 * 5-Star: Handles defined in backend node_config.py
 */
import { DEFAULTS } from '@/config/defaults'

export default {
  type: 'subflow',

  // Default parameters
  getDefaultParams: () => ({
    workflowRef: '',
    executionMode: 'inline',
    inputMapping: {},
    outputMapping: {},
    timeoutMs: DEFAULTS.TIMEOUTS.SUBFLOW_NODE
  }),

  // Style
  styleClass: 'subflow-node',
  isFlowControl: true,

  // Subflow-specific flag
  isSubflow: true,

  // Parameter editor component
  paramsComponent: 'GenericParams',

  // Show add button after subflow
  showAddButton: true,

  // Helper to check if workflowRef is set
  hasWorkflowRef: (params) => {
    return !!params?.workflowRef
  }
}
