/**
 * Keyboard Shortcuts Module
 *
 * S-Grade: Re-export all keyboard shortcut functionality.
 *
 * Split modules:
 * - constants.js: Platform detection and default shortcuts
 * - useClipboard.js: Clipboard operations
 * - useHistory.js: Undo/redo history
 * - useKeyboardShortcutsCore.js: Main composable
 */

// Main composable
export { useKeyboardShortcuts } from './useKeyboardShortcutsCore'

// Support composables
export { useClipboard } from './useClipboard'
export { useHistory } from './useHistory'

// Constants
export { isMac, hasModifier, DEFAULT_SHORTCUTS } from './constants'

// Default export
export { useKeyboardShortcuts as default } from './useKeyboardShortcutsCore'
