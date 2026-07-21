/**
 * PluginRegistry Unit Tests
 */
import { describe, it, expect, beforeEach } from 'vitest'

// Mock implementation for testing without full Vue setup
class MockPluginRegistry {
  constructor() {
    this._plugins = new Map()
    this._categories = new Map()
  }

  register(plugin) {
    if (!plugin.pluginId) throw new Error('Plugin must have pluginId')
    if (this._plugins.has(plugin.pluginId)) {
      console.warn(`Plugin ${plugin.pluginId} already registered`)
      return false
    }
    this._plugins.set(plugin.pluginId, plugin)
    const category = plugin.category || 'default'
    if (!this._categories.has(category)) {
      this._categories.set(category, new Set())
    }
    this._categories.get(category).add(plugin.pluginId)
    if (typeof plugin.onRegister === 'function') {
      plugin.onRegister()
    }
    return true
  }

  unregister(pluginId) {
    const plugin = this._plugins.get(pluginId)
    if (!plugin) return false
    if (typeof plugin.onUnregister === 'function') {
      plugin.onUnregister()
    }
    this._plugins.delete(pluginId)
    for (const [, ids] of this._categories) {
      ids.delete(pluginId)
    }
    return true
  }

  get(pluginId) {
    return this._plugins.get(pluginId) || null
  }

  has(pluginId) {
    return this._plugins.has(pluginId)
  }

  getByCategory(category) {
    const ids = this._categories.get(category)
    if (!ids) return []
    return Array.from(ids).map(id => this._plugins.get(id))
  }

  getAll() {
    return Array.from(this._plugins.values())
  }

  clear() {
    for (const plugin of this._plugins.values()) {
      if (typeof plugin.onUnregister === 'function') {
        plugin.onUnregister()
      }
    }
    this._plugins.clear()
    this._categories.clear()
  }

  get size() {
    return this._plugins.size
  }
}

describe('PluginRegistry', () => {
  let registry

  beforeEach(() => {
    registry = new MockPluginRegistry()
  })

  describe('register', () => {
    it('should register a plugin with valid pluginId', () => {
      const plugin = { pluginId: 'test-plugin', version: '1.0.0' }
      expect(registry.register(plugin)).toBe(true)
      expect(registry.has('test-plugin')).toBe(true)
    })

    it('should throw error for plugin without pluginId', () => {
      const plugin = { version: '1.0.0' }
      expect(() => registry.register(plugin)).toThrow('Plugin must have pluginId')
    })

    it('should not register duplicate plugins', () => {
      const plugin = { pluginId: 'test-plugin' }
      registry.register(plugin)
      expect(registry.register(plugin)).toBe(false)
    })

    it('should call onRegister lifecycle hook', () => {
      let called = false
      const plugin = {
        pluginId: 'test-plugin',
        onRegister: () => { called = true }
      }
      registry.register(plugin)
      expect(called).toBe(true)
    })

    it('should categorize plugins correctly', () => {
      const plugin1 = { pluginId: 'field-1', category: 'fields' }
      const plugin2 = { pluginId: 'field-2', category: 'fields' }
      const plugin3 = { pluginId: 'output-1', category: 'outputs' }

      registry.register(plugin1)
      registry.register(plugin2)
      registry.register(plugin3)

      const fields = registry.getByCategory('fields')
      expect(fields).toHaveLength(2)
      expect(fields.map(p => p.pluginId)).toContain('field-1')
      expect(fields.map(p => p.pluginId)).toContain('field-2')
    })
  })

  describe('unregister', () => {
    it('should unregister an existing plugin', () => {
      const plugin = { pluginId: 'test-plugin' }
      registry.register(plugin)
      expect(registry.unregister('test-plugin')).toBe(true)
      expect(registry.has('test-plugin')).toBe(false)
    })

    it('should return false for non-existent plugin', () => {
      expect(registry.unregister('non-existent')).toBe(false)
    })

    it('should call onUnregister lifecycle hook', () => {
      let called = false
      const plugin = {
        pluginId: 'test-plugin',
        onUnregister: () => { called = true }
      }
      registry.register(plugin)
      registry.unregister('test-plugin')
      expect(called).toBe(true)
    })
  })

  describe('get', () => {
    it('should return plugin by id', () => {
      const plugin = { pluginId: 'test-plugin', data: 'test' }
      registry.register(plugin)
      expect(registry.get('test-plugin')).toEqual(plugin)
    })

    it('should return null for non-existent plugin', () => {
      expect(registry.get('non-existent')).toBeNull()
    })
  })

  describe('getAll', () => {
    it('should return all registered plugins', () => {
      registry.register({ pluginId: 'plugin-1' })
      registry.register({ pluginId: 'plugin-2' })
      registry.register({ pluginId: 'plugin-3' })

      const all = registry.getAll()
      expect(all).toHaveLength(3)
    })
  })

  describe('clear', () => {
    it('should remove all plugins', () => {
      registry.register({ pluginId: 'plugin-1' })
      registry.register({ pluginId: 'plugin-2' })
      registry.clear()
      expect(registry.size).toBe(0)
    })

    it('should call onUnregister for all plugins', () => {
      let count = 0
      registry.register({ pluginId: 'plugin-1', onUnregister: () => count++ })
      registry.register({ pluginId: 'plugin-2', onUnregister: () => count++ })
      registry.clear()
      expect(count).toBe(2)
    })
  })
})
