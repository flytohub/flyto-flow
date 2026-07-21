/**
 * Plugin System Initialization
 * Called once at app startup to register all plugins
 */

import { PluginRegistry } from './core/PluginRegistry'
import { RendererResolver } from './core/RendererResolver'

// Track initialization state
let initialized = false

/**
 * Initialize the plugin system
 * @param {Object} options - Initialization options
 */
export async function initPlugins(options = {}) {
  if (initialized && !options.force) {
    return
  }


  // Clear existing if reinitializing
  if (options.force) {
    PluginRegistry.clear()
    RendererResolver.clearCache()
  }

  // Register built-in plugins
  await registerBuiltinPlugins()

  // Log stats
  const stats = {
    fieldRenderers: PluginRegistry.count('fieldRenderer'),
    outputRenderers: PluginRegistry.count('outputRenderer'),
    params: PluginRegistry.count('params'),
    total: PluginRegistry.count(),
  }


  initialized = true
}

/**
 * Register all built-in plugins
 * @private
 */
async function registerBuiltinPlugins() {
  try {
    // Register field renderers
    const { registerFieldRenderers } = await import(
      '@/components/templateBuilder/preview/renderers/index.js'
    )
    registerFieldRenderers()
  } catch (e) {
  }
}

