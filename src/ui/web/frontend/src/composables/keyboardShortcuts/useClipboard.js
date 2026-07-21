/**
 * Clipboard Composable
 *
 * S-Grade: Simple clipboard operations.
 * Single responsibility: Copy, paste, clear clipboard data.
 */

import { ref, computed } from 'vue'

/**
 * Simple clipboard operations
 */
export function useClipboard() {
  const clipboardData = ref(null)

  function copy(data) {
    clipboardData.value = JSON.parse(JSON.stringify(data))
    return true
  }

  function paste() {
    if (!clipboardData.value) return null
    return JSON.parse(JSON.stringify(clipboardData.value))
  }

  function clear() {
    clipboardData.value = null
  }

  const hasData = computed(() => clipboardData.value !== null)

  return {
    copy,
    paste,
    clear,
    hasData,
  }
}
