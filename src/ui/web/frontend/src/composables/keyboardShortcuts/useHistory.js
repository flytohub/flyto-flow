/**
 * History Composable
 *
 * S-Grade: Undo/Redo history management.
 * Single responsibility: Track state history for undo/redo.
 */

import { ref, computed } from 'vue'

/**
 * Undo/Redo history management
 */
export function useHistory(options = {}) {
  const { maxSize = 50 } = options

  const history = ref([])
  const currentIndex = ref(-1)

  const canUndo = computed(() => currentIndex.value > 0)
  const canRedo = computed(() => currentIndex.value < history.value.length - 1)

  function push(state) {
    // Remove any future states if we're not at the end
    if (currentIndex.value < history.value.length - 1) {
      history.value = history.value.slice(0, currentIndex.value + 1)
    }

    // Add new state
    history.value.push(JSON.parse(JSON.stringify(state)))
    currentIndex.value = history.value.length - 1

    // Trim if exceeds max size
    if (history.value.length > maxSize) {
      history.value.shift()
      currentIndex.value--
    }
  }

  function undo() {
    if (!canUndo.value) return null
    currentIndex.value--
    return JSON.parse(JSON.stringify(history.value[currentIndex.value]))
  }

  function redo() {
    if (!canRedo.value) return null
    currentIndex.value++
    return JSON.parse(JSON.stringify(history.value[currentIndex.value]))
  }

  function clear() {
    history.value = []
    currentIndex.value = -1
  }

  return {
    push,
    undo,
    redo,
    clear,
    canUndo,
    canRedo,
    historySize: computed(() => history.value.length),
  }
}
