/**
 * Plugin Registry
 * Central registration and lookup for all plugins
 */

import { isValidPlugin } from './PluginInterface'

class PluginRegistryClass {
  constructor() {
    /** @type {Map<string, any>} */
    this._plugins = new Map()

    /** @type {Map<string, Function>} */
    this._resolvers = new Map()

    /** @type {Set<string>} */
    this._categories = new Set()
  }

  /**
   * Build a registry key from category and id
   * @private
   */
  _buildKey(pluginId, category = 'default') {
    return `${category}:${pluginId}`
  }

  /**
   * Register a plugin
   * @param {Object} plugin - Plugin to register
   * @param {string} category - Plugin category
   * @returns {this}
   */
  register(plugin, category = 'default') {
    const pluginId = plugin.pluginId || plugin.id

    if (!pluginId) {
      throw new Error('Plugin must have pluginId')
    }

    const key = this._buildKey(pluginId, category)

    if (this._plugins.has(key)) {
    }

    this._plugins.set(key, plugin)
    this._categories.add(category)

    // Call lifecycle hook
    if (typeof plugin.onRegister === 'function') {
      plugin.onRegister(this)
    }

    return this
  }

  /**
   * Register multiple plugins
   * @param {Object[]} plugins - Plugins to register
   * @param {string} category - Plugin category
   * @returns {this}
   */
  registerAll(plugins, category = 'default') {
    plugins.forEach(plugin => this.register(plugin, category))
    return this
  }

  /**
   * Unregister a plugin
   * @param {string} pluginId - Plugin ID
   * @param {string} category - Plugin category
   * @returns {this}
   */
  unregister(pluginId, category = 'default') {
    const key = this._buildKey(pluginId, category)
    const plugin = this._plugins.get(key)

    if (plugin) {
      if (typeof plugin.onUnregister === 'function') {
        plugin.onUnregister(this)
      }
      this._plugins.delete(key)
    }

    return this
  }

  /**
   * Get a plugin by ID
   * @param {string} pluginId - Plugin ID
   * @param {string} category - Plugin category
   * @returns {Object|undefined}
   */
  get(pluginId, category = 'default') {
    return this._plugins.get(this._buildKey(pluginId, category))
  }

  /**
   * Check if a plugin exists
   * @param {string} pluginId - Plugin ID
   * @param {string} category - Plugin category
   * @returns {boolean}
   */
  has(pluginId, category = 'default') {
    return this._plugins.has(this._buildKey(pluginId, category))
  }

  /**
   * Get all plugins, optionally filtered by category
   * @param {string|null} category - Optional category filter
   * @returns {Object[]}
   */
  getAll(category = null) {
    if (!category) {
      return Array.from(this._plugins.values())
    }

    const prefix = `${category}:`
    return Array.from(this._plugins.entries())
      .filter(([key]) => key.startsWith(prefix))
      .map(([, plugin]) => plugin)
  }

  /**
   * Get all registered categories
   * @returns {string[]}
   */
  getCategories() {
    return Array.from(this._categories)
  }

  /**
   * Get plugin count
   * @param {string|null} category - Optional category filter
   * @returns {number}
   */
  count(category = null) {
    return this.getAll(category).length
  }

  /**
   * Register a custom resolver for a category
   * @param {string} category - Category name
   * @param {Function} resolver - Resolver function
   */
  registerResolver(category, resolver) {
    this._resolvers.set(category, resolver)
  }

  /**
   * Resolve a plugin using category resolver
   * @param {string} category - Category name
   * @param {string} type - Type to resolve
   * @returns {any}
   */
  resolve(category, type) {
    const resolver = this._resolvers.get(category)
    if (resolver) {
      return resolver(type, this)
    }
    return this.get(type, category)
  }

  /**
   * Clear all plugins (useful for testing)
   */
  clear() {
    this._plugins.clear()
    this._resolvers.clear()
    this._categories.clear()
  }
}

// Singleton instance
export const PluginRegistry = new PluginRegistryClass()

export default PluginRegistry
