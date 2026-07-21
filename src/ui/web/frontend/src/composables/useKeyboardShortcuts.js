/**
 * Keyboard Shortcuts Composable
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All keyboard shortcut logic split into keyboardShortcuts/* directory.
 *
 * Split modules:
 * - keyboardShortcuts/constants.js: Platform detection and defaults
 * - keyboardShortcuts/useClipboard.js: Clipboard operations
 * - keyboardShortcuts/useHistory.js: Undo/redo history
 * - keyboardShortcuts/useKeyboardShortcutsCore.js: Main composable
 */

// Re-export all from split modules
export {
  useKeyboardShortcuts,
  useClipboard,
  useHistory,
  isMac,
  hasModifier,
  DEFAULT_SHORTCUTS
} from './keyboardShortcuts/index'

export { useKeyboardShortcuts as default } from './keyboardShortcuts/index'
