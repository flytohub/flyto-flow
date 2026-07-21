/**
 * Keyboard Shortcuts Constants
 *
 * S-Grade: Platform detection and default shortcuts.
 * Single responsibility: Define shortcut constants.
 */

/**
 * Platform detection for modifier key
 */
export const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform)

/**
 * Check if modifier key is pressed (Cmd on Mac, Ctrl on Windows/Linux)
 */
export function hasModifier(e) {
  return isMac ? e.metaKey : e.ctrlKey
}

/**
 * Default shortcut definitions
 */
export const DEFAULT_SHORTCUTS = {
  copy: { key: 'c', modifier: true, description: 'Copy selected' },
  cut: { key: 'x', modifier: true, description: 'Cut selected' },
  paste: { key: 'v', modifier: true, description: 'Paste' },
  undo: { key: 'z', modifier: true, description: 'Undo' },
  redo: { key: 'z', modifier: true, shift: true, description: 'Redo' },
  delete: { key: ['Delete', 'Backspace'], modifier: false, description: 'Delete selected' },
  save: { key: 's', modifier: true, description: 'Save' },
  selectAll: { key: 'a', modifier: true, description: 'Select all' },
  escape: { key: 'Escape', modifier: false, description: 'Cancel/Close' },
  duplicate: { key: 'd', modifier: true, description: 'Duplicate selected' },
  // Arrow keys for node movement
  moveUp: { key: 'ArrowUp', modifier: false, description: 'Move selection up' },
  moveDown: { key: 'ArrowDown', modifier: false, description: 'Move selection down' },
  moveLeft: { key: 'ArrowLeft', modifier: false, description: 'Move selection left' },
  moveRight: { key: 'ArrowRight', modifier: false, description: 'Move selection right' },
}
