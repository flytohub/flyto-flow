/**
 * Template Builder Keyboard Shortcuts
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All keyboard shortcuts logic split into builderKeyboardShortcuts/* directory.
 *
 * Split modules:
 * - builderKeyboardShortcuts/handlers.js: Action handlers
 * - builderKeyboardShortcuts/useBuilderKeyboardShortcutsCore.js: Main composable
 */

// Re-export all from split modules
export { useBuilderKeyboardShortcuts } from './builderKeyboardShortcuts/index'
