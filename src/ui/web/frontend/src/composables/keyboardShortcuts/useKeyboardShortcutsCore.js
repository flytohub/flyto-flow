/**
 * Keyboard Shortcuts Core
 *
 * S-Grade: Main keyboard shortcut composable.
 * Single responsibility: Handle keyboard events and match shortcuts.
 */

import { onMounted, onUnmounted, ref, computed } from 'vue'
import { isMac, hasModifier, DEFAULT_SHORTCUTS } from './constants'

/**
 * Hook for keyboard shortcuts
 *
 * @param {Object} handlers - Map of action names to handler functions
 * @param {Object} options - Configuration options
 * @returns {Object} Shortcut utilities
 */
export function useKeyboardShortcuts(handlers = {}, options = {}) {
  const {
    enabled = ref(true),
    preventDefault = true,
    shortcuts = DEFAULT_SHORTCUTS,
    ignoreInputs = true,
  } = options

  const activeShortcuts = ref(new Set())
  const lastTriggered = ref(null)

  /**
   * Check if event target is an input element
   */
  function isInputElement(target) {
    if (!ignoreInputs) return false
    const tagName = target?.tagName?.toLowerCase()
    return (
      tagName === 'input' ||
      tagName === 'textarea' ||
      tagName === 'select' ||
      target?.isContentEditable
    )
  }

  /**
   * Match keyboard event to shortcut definition
   */
  function matchShortcut(e, shortcut) {
    const keys = Array.isArray(shortcut.key) ? shortcut.key : [shortcut.key]
    const keyMatch = keys.some(k => k.toLowerCase() === e.key.toLowerCase())

    if (!keyMatch) return false
    if (shortcut.modifier && !hasModifier(e)) return false
    if (!shortcut.modifier && hasModifier(e)) return false
    if (shortcut.shift && !e.shiftKey) return false
    if (!shortcut.shift && e.shiftKey && shortcut.modifier) return false

    return true
  }

  /**
   * Handle keydown event
   */
  function handleKeyDown(e) {
    // Skip if disabled or in input
    if (!enabled.value) return
    if (isInputElement(e.target)) return

    // Find matching shortcut
    for (const [action, shortcut] of Object.entries(shortcuts)) {
      if (matchShortcut(e, shortcut)) {
        const handler = handlers[action]
        if (handler) {
          if (preventDefault) {
            e.preventDefault()
            e.stopPropagation()
          }

          activeShortcuts.value.add(action)
          lastTriggered.value = { action, timestamp: Date.now() }

          // Execute handler
          try {
            handler(e)
          } catch (err) {
          }

          // Remove from active after brief delay
          setTimeout(() => {
            activeShortcuts.value.delete(action)
          }, 100)

          return
        }
      }
    }
  }

  /**
   * Get display string for a shortcut
   */
  function getShortcutDisplay(action) {
    const shortcut = shortcuts[action]
    if (!shortcut) return ''

    const parts = []
    if (shortcut.modifier) {
      parts.push(isMac ? '⌘' : 'Ctrl')
    }
    if (shortcut.shift) {
      parts.push(isMac ? '⇧' : 'Shift')
    }

    const key = Array.isArray(shortcut.key) ? shortcut.key[0] : shortcut.key
    parts.push(key.length === 1 ? key.toUpperCase() : key)

    return parts.join(isMac ? '' : '+')
  }

  /**
   * Get all available shortcuts for display
   */
  const availableShortcuts = computed(() => {
    return Object.entries(shortcuts)
      .filter(([action]) => handlers[action])
      .map(([action, shortcut]) => ({
        action,
        display: getShortcutDisplay(action),
        description: shortcut.description,
      }))
  })

  // Setup and cleanup
  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown)
  })

  return {
    activeShortcuts,
    lastTriggered,
    availableShortcuts,
    getShortcutDisplay,
    isMac,
  }
}
