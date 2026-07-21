/**
 * Plugin Interface
 * Base class that all plugins must extend
 */

export class PluginInterface {
  /**
   * Unique plugin identifier (required)
   * @type {string}
   */
  static get pluginId() {
    throw new Error('Plugin must define pluginId')
  }

  /**
   * Plugin version
   * @type {string}
   */
  static get version() {
    return '1.0.0'
  }

  /**
   * Display name for UI
   * @type {string}
   */
  static get displayName() {
    return this.pluginId
  }

  /**
   * Plugin category for grouping
   * @type {string}
   */
  static get category() {
    return 'default'
  }

  /**
   * Plugin description
   * @type {string}
   */
  static get description() {
    return ''
  }

  /**
   * Plugin dependencies (other plugin IDs)
   * @type {string[]}
   */
  static get dependencies() {
    return []
  }

  /**
   * Called when plugin is registered
   * @param {PluginRegistry} registry - The plugin registry
   */
  static onRegister(registry) {
    // Override in subclass if needed
  }

  /**
   * Called when plugin is unregistered
   * @param {PluginRegistry} registry - The plugin registry
   */
  static onUnregister(registry) {
    // Override in subclass if needed
  }

  /**
   * Validate plugin configuration
   * @param {Object} data - Data to validate
   * @returns {{ valid: boolean, errors: string[], warnings: string[] }}
   */
  static validate(data) {
    return { valid: true, errors: [], warnings: [] }
  }

  /**
   * Get default configuration
   * @returns {Object}
   */
  static getDefaults() {
    return {}
  }
}

/**
 * Check if a class properly implements PluginInterface
 * @param {Function} PluginClass - Class to check
 * @returns {boolean}
 */
export function isValidPlugin(PluginClass) {
  try {
    return (
      typeof PluginClass.pluginId === 'string' &&
      PluginClass.pluginId.length > 0
    )
  } catch {
    return false
  }
}
