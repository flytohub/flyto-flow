/**
 * Builder Keyboard Shortcuts Module
 *
 * S-Grade: Re-export all builder keyboard shortcuts functionality.
 *
 * Split modules:
 * - handlers.js: Keyboard shortcut action handlers
 * - useBuilderKeyboardShortcutsCore.js: Main composable
 */

// Main composable
export { useBuilderKeyboardShortcuts } from './useBuilderKeyboardShortcutsCore'

// Handlers (for testing/advanced usage)
export { createHandlers } from './handlers'
