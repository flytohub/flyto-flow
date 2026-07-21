/**
 * Loop Node - Explicit loop control (foreach items)
 *
 * Handle semantics (fixed naming, consistent across Core/Cloud/Pro):
 * - in (left gray): External control flow enters loop
 * - body_out (bottom blue): Enter loop body (sub-port, creates scope: loop.item / loop.index)
 * - done_out (right green): Continue after loop completes
 *
 * 5-Star: Handles defined in backend node_config.py
 */
export default {
  type: 'loop',

  // Default parameters
  getDefaultParams: () => ({
    items: '',      // Foreach source (array or variable reference)
    as: 'item',     // Alias for loop.item (optional)
    indexAs: 'index'  // Alias for loop.index (optional)
  }),

  // Scope definition (created by Core executor)
  getLoopScope: (item, index, total) => ({
    item,
    index,
    total,
    iteration: index + 1,
    isFirst: index === 0,
    isLast: index === total - 1
  }),

  // Style
  styleClass: 'loop-node',
  isFlowControl: true,
  isLoop: true,

  // Params editor component
  paramsComponent: 'FlowControlParams',

  // Show add button
  showAddButton: true,

  // Validation rules
  validation: {
    // body_out must be connected
    bodyOutRequired: true,
  }
}
