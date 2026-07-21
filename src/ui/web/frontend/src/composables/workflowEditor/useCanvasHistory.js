/**
 * Canvas History Composable
 * Provides Undo/Redo functionality for workflow canvas operations
 *
 * Features:
 * - Tracks node add/delete/move operations
 * - Tracks edge add/delete operations
 * - Supports Ctrl+Z (undo) and Ctrl+Shift+Z (redo)
 * - Maximum history limit to prevent memory issues
 */

import { ref, computed } from 'vue'

/**
 * Action types for history tracking
 */
export const HISTORY_ACTIONS = {
  NODE_ADD: 'node_add',
  NODE_DELETE: 'node_delete',
  NODE_MOVE: 'node_move',
  NODE_UPDATE: 'node_update',
  EDGE_ADD: 'edge_add',
  EDGE_DELETE: 'edge_delete',
  BATCH: 'batch'
}

/**
 * Creates a canvas history manager
 * @param {Object} options - Configuration options
 * @param {number} options.maxHistory - Maximum number of history entries (default: 50)
 * @returns {Object} History management functions
 */
export function useCanvasHistory(options = {}) {
  const { maxHistory = 50 } = options

  // History stacks
  const undoStack = ref([])
  const redoStack = ref([])

  // Track if we're currently performing undo/redo to prevent recursive saves
  const isUndoRedoInProgress = ref(false)

  /**
   * Deep clone an object (used to save state)
   */
  function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj))
  }

  /**
   * Save a state snapshot to the undo stack
   * @param {string} action - The action type (from HISTORY_ACTIONS)
   * @param {Object} state - The state to save { nodes, edges }
   * @param {Object} metadata - Optional metadata about the change
   */
  function pushState(action, state, metadata = {}) {
    // Don't save state during undo/redo operations
    if (isUndoRedoInProgress.value) return

    const snapshot = {
      action,
      timestamp: Date.now(),
      nodes: deepClone(state.nodes || []),
      edges: deepClone(state.edges || []),
      metadata
    }

    undoStack.value.push(snapshot)

    // Limit history size
    if (undoStack.value.length > maxHistory) {
      undoStack.value.shift()
    }

    // Clear redo stack when new action is performed
    redoStack.value = []
  }

  /**
   * Undo the last action
   * @param {Object} currentState - Current state { nodes, edges }
   * @returns {Object|null} The restored state or null if nothing to undo
   */
  function undo(currentState) {
    if (undoStack.value.length === 0) return null

    isUndoRedoInProgress.value = true

    try {
      // Save current state to redo stack before undoing
      const currentSnapshot = {
        action: 'redo_point',
        timestamp: Date.now(),
        nodes: deepClone(currentState.nodes || []),
        edges: deepClone(currentState.edges || [])
      }
      redoStack.value.push(currentSnapshot)

      // Pop the last state from undo stack
      const previousState = undoStack.value.pop()

      return {
        nodes: deepClone(previousState.nodes),
        edges: deepClone(previousState.edges),
        action: previousState.action
      }
    } finally {
      isUndoRedoInProgress.value = false
    }
  }

  /**
   * Redo the last undone action
   * @param {Object} currentState - Current state { nodes, edges }
   * @returns {Object|null} The restored state or null if nothing to redo
   */
  function redo(currentState) {
    if (redoStack.value.length === 0) return null

    isUndoRedoInProgress.value = true

    try {
      // Save current state to undo stack before redoing
      const currentSnapshot = {
        action: 'undo_point',
        timestamp: Date.now(),
        nodes: deepClone(currentState.nodes || []),
        edges: deepClone(currentState.edges || [])
      }
      undoStack.value.push(currentSnapshot)

      // Pop the last state from redo stack
      const nextState = redoStack.value.pop()

      return {
        nodes: deepClone(nextState.nodes),
        edges: deepClone(nextState.edges),
        action: nextState.action
      }
    } finally {
      isUndoRedoInProgress.value = false
    }
  }

  /**
   * Clear all history
   */
  function clearHistory() {
    undoStack.value = []
    redoStack.value = []
  }

  /**
   * Check if undo is available
   */
  const canUndo = computed(() => undoStack.value.length > 0)

  /**
   * Check if redo is available
   */
  const canRedo = computed(() => redoStack.value.length > 0)

  /**
   * Get the number of undo steps available
   */
  const undoCount = computed(() => undoStack.value.length)

  /**
   * Get the number of redo steps available
   */
  const redoCount = computed(() => redoStack.value.length)

  /**
   * Get the last action description (for UI display)
   */
  const lastAction = computed(() => {
    if (undoStack.value.length === 0) return null
    const last = undoStack.value[undoStack.value.length - 1]
    return {
      action: last.action,
      metadata: last.metadata
    }
  })

  return {
    // State
    undoStack,
    redoStack,
    canUndo,
    canRedo,
    undoCount,
    redoCount,
    lastAction,
    isUndoRedoInProgress,

    // Actions
    pushState,
    undo,
    redo,
    clearHistory,

    // Constants
    HISTORY_ACTIONS
  }
}

export default useCanvasHistory
