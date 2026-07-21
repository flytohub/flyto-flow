/**
 * Renderer Resolver
 * Resolves component types to their Vue renderer components
 */

import { markRaw, defineAsyncComponent } from 'vue'
import { PluginRegistry } from './PluginRegistry'

class RendererResolverClass {
  constructor() {
    /** @type {Map<string, any>} */
    this._fallbacks = new Map()

    /** @type {Map<string, any>} */
    this._cache = new Map()
  }

  /**
   * Set fallback component for a category
   * @param {string} category - Category name
   * @param {Object} component - Vue component
   */
  setFallback(category, component) {
    this._fallbacks.set(category, markRaw(component))
  }

  /**
   * Get fallback component for a category
   * @param {string} category - Category name
   * @returns {Object|null}
   */
  getFallback(category) {
    return this._fallbacks.get(category) || null
  }

  /**
   * Resolve a type to its renderer component
   * @param {string} type - Type to resolve
   * @param {string} category - Plugin category
   * @returns {Object|null}
   */
  resolve(type, category = 'fieldRenderer') {
    // Check cache first
    const cacheKey = `${category}:${type}`
    if (this._cache.has(cacheKey)) {
      return this._cache.get(cacheKey)
    }

    // Look up plugin
    const plugin = PluginRegistry.get(type, category)

    if (plugin?.component) {
      const component = markRaw(plugin.component)
      this._cache.set(cacheKey, component)
      return component
    }

    // Try resolver
    const resolved = PluginRegistry.resolve(category, type)
    if (resolved?.component) {
      const component = markRaw(resolved.component)
      this._cache.set(cacheKey, component)
      return component
    }

    // Return fallback
    return this.getFallback(category)
  }

  /**
   * Resolve default props for a type
   * @param {string} type - Type to resolve
   * @param {string} category - Plugin category
   * @returns {Object}
   */
  resolveProps(type, category = 'fieldRenderer') {
    const plugin = PluginRegistry.get(type, category)
    return plugin?.defaultProps || plugin?.getDefaults?.() || {}
  }

  /**
   * Check if a type is supported
   * @param {string} type - Type to check
   * @param {string} category - Plugin category
   * @returns {boolean}
   */
  supports(type, category = 'fieldRenderer') {
    return PluginRegistry.has(type, category)
  }

  /**
   * Get all supported types for a category
   * @param {string} category - Plugin category
   * @returns {string[]}
   */
  getTypes(category = 'fieldRenderer') {
    return PluginRegistry.getAll(category)
      .map(p => p.pluginId || p.id)
      .filter(Boolean)
  }

  /**
   * Get all plugins for a category
   * @param {string} category - Plugin category
   * @returns {Object[]}
   */
  getAll(category = 'fieldRenderer') {
    return PluginRegistry.getAll(category)
  }

  /**
   * Create an async component loader
   * @param {Function} loader - Import function
   * @returns {Object} Async component
   */
  createAsyncComponent(loader) {
    return markRaw(defineAsyncComponent(loader))
  }

  /**
   * Clear the resolver cache
   */
  clearCache() {
    this._cache.clear()
  }
}

// Singleton instance
export const RendererResolver = new RendererResolverClass()

export default RendererResolver
