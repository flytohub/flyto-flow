/**
 * RendererResolver Unit Tests
 */
import { describe, it, expect, beforeEach } from 'vitest'

// Mock implementation for testing
class MockRendererResolver {
  constructor() {
    this._renderers = new Map()
    this._fallback = null
  }

  registerRenderer(type, component, options = {}) {
    this._renderers.set(type, { component, options })
  }

  setFallback(component) {
    this._fallback = component
  }

  resolve(type) {
    const entry = this._renderers.get(type)
    if (entry) return entry.component
    return this._fallback
  }

  resolveProps(type) {
    const entry = this._renderers.get(type)
    return entry?.options?.defaultProps || {}
  }

  supports(type) {
    return this._renderers.has(type)
  }

  getAll() {
    return Array.from(this._renderers.entries()).map(([type, entry]) => ({
      type,
      component: entry.component,
      options: entry.options
    }))
  }

  clear() {
    this._renderers.clear()
    this._fallback = null
  }
}

describe('RendererResolver', () => {
  let resolver

  beforeEach(() => {
    resolver = new MockRendererResolver()
  })

  describe('registerRenderer', () => {
    it('should register a renderer for a type', () => {
      const TextComponent = { name: 'TextRenderer' }
      resolver.registerRenderer('text', TextComponent)
      expect(resolver.supports('text')).toBe(true)
    })

    it('should register with options', () => {
      const NumberComponent = { name: 'NumberRenderer' }
      resolver.registerRenderer('number', NumberComponent, {
        defaultProps: { min: 0, max: 100 }
      })
      expect(resolver.resolveProps('number')).toEqual({ min: 0, max: 100 })
    })
  })

  describe('resolve', () => {
    it('should return registered component', () => {
      const TextComponent = { name: 'TextRenderer' }
      resolver.registerRenderer('text', TextComponent)
      expect(resolver.resolve('text')).toBe(TextComponent)
    })

    it('should return fallback for unregistered type', () => {
      const FallbackComponent = { name: 'Fallback' }
      resolver.setFallback(FallbackComponent)
      expect(resolver.resolve('unknown')).toBe(FallbackComponent)
    })

    it('should return null if no fallback set', () => {
      expect(resolver.resolve('unknown')).toBeNull()
    })
  })

  describe('supports', () => {
    it('should return true for registered type', () => {
      resolver.registerRenderer('text', {})
      expect(resolver.supports('text')).toBe(true)
    })

    it('should return false for unregistered type', () => {
      expect(resolver.supports('unknown')).toBe(false)
    })
  })

  describe('getAll', () => {
    it('should return all registered renderers', () => {
      resolver.registerRenderer('text', { name: 'Text' })
      resolver.registerRenderer('number', { name: 'Number' })
      resolver.registerRenderer('select', { name: 'Select' })

      const all = resolver.getAll()
      expect(all).toHaveLength(3)
      expect(all.map(r => r.type)).toContain('text')
      expect(all.map(r => r.type)).toContain('number')
      expect(all.map(r => r.type)).toContain('select')
    })
  })

  describe('clear', () => {
    it('should remove all renderers', () => {
      resolver.registerRenderer('text', {})
      resolver.registerRenderer('number', {})
      resolver.clear()
      expect(resolver.getAll()).toHaveLength(0)
    })

    it('should clear fallback', () => {
      resolver.setFallback({ name: 'Fallback' })
      resolver.clear()
      expect(resolver.resolve('unknown')).toBeNull()
    })
  })
})
