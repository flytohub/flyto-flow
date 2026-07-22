import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/modules', () => ({
  getTieredCatalog: vi.fn()
}))

import { useModulesStore } from '@/stores/modulesStore'
import { getTieredCatalog } from '@/api/modules'

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] ?? null),
    setItem: vi.fn((key, val) => { store[key] = val }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: () => { store = {} }
  }
})()
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

describe('useModulesStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useModulesStore()
    vi.clearAllMocks()
    localStorageMock.clear()
  })

  // ==========================================================================
  // Initial State
  // ==========================================================================
  describe('initial state', () => {
    it('has correct defaults', () => {
      expect(store.availableSteps).toEqual({})
      expect(store.moduleCategories).toEqual([])
      expect(store.modulesMetadata).toEqual({})
      expect(store.defaultModulesList).toEqual([])
      expect(store.expertModulesList).toEqual([])
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.hasLoaded).toBe(false)
      expect(store.isReady).toBe(false)
    })
  })

  // ==========================================================================
  // Getters
  // ==========================================================================
  describe('getters', () => {
    it('hasModules returns false when empty', () => {
      expect(store.hasModules).toBe(false)
    })

    it('hasModules returns true when modules exist', () => {
      store.modulesMetadata = { 'mod-1': { id: 'mod-1' } }
      expect(store.hasModules).toBe(true)
    })

    it('getModuleById returns module by id', () => {
      store.modulesMetadata = { 'mod-1': { id: 'mod-1', name: 'Test' } }
      expect(store.getModuleById('mod-1')).toEqual({ id: 'mod-1', name: 'Test' })
    })

    it('getModuleById returns undefined for missing id', () => {
      expect(store.getModuleById('missing')).toBeUndefined()
    })

    it('getModulesByCategory returns modules for category', () => {
      store.availableSteps = { browser: [{ id: 'mod-1' }] }
      expect(store.getModulesByCategory('browser')).toEqual([{ id: 'mod-1' }])
    })

    it('getModulesByCategory returns empty array for missing category', () => {
      expect(store.getModulesByCategory('nonexistent')).toEqual([])
    })
  })

  // ==========================================================================
  // loadModules
  // ==========================================================================
  describe('loadModules', () => {
    const mockResponse = {
      default: { modules: [{ id: 'mod-1' }] },
      expert: { modules: [{ id: 'mod-e1' }] },
      modulesByCategory: { browser: [{ id: 'mod-1' }] },
      moduleCategories: ['browser'],
      modulesMetadata: { 'mod-1': { id: 'mod-1' }, 'mod-e1': { id: 'mod-e1' } },
      version: '1.0'
    }

    it('fetches from API and hydrates store', async () => {
      getTieredCatalog.mockResolvedValue(mockResponse)

      const result = await store.loadModules('en')

      expect(result).toEqual({ ok: true })
      expect(store.defaultModulesList).toEqual([{ id: 'mod-1' }])
      expect(store.expertModulesList).toEqual([{ id: 'mod-e1' }])
      expect(store.moduleCategories).toEqual(['browser'])
      expect(store.modulesMetadata).toEqual({ 'mod-1': { id: 'mod-1' }, 'mod-e1': { id: 'mod-e1' } })
      expect(store.isLoading).toBe(false)
      expect(store.hasLoaded).toBe(true)
      expect(store.isReady).toBe(true)
    })

    it('hydrates raw snake_case catalog responses', async () => {
      getTieredCatalog.mockResolvedValue({
        default: { modules: [{ id: 'mod-1' }] },
        expert: { modules: [{ id: 'mod-e1' }] },
        modules_by_category: { browser: [{ id: 'mod-1' }] },
        module_categories: ['browser'],
        modules_metadata: { 'mod-1': { id: 'mod-1' }, 'mod-e1': { id: 'mod-e1' } },
        version: '1.0'
      })

      const result = await store.loadModules('en')

      expect(result).toEqual({ ok: true })
      expect(store.availableSteps).toEqual({ browser: [{ id: 'mod-1' }] })
      expect(store.moduleCategories).toEqual(['browser'])
      expect(store.modulesMetadata).toEqual({ 'mod-1': { id: 'mod-1' }, 'mod-e1': { id: 'mod-e1' } })
    })

    it('keeps stable empty shapes for partial catalog responses', async () => {
      getTieredCatalog.mockResolvedValue({
        ok: true,
        default: null,
        expert: { modules: 'bad' },
        modules_by_category: null,
        module_categories: 'bad',
        modules_metadata: { 'browser.goto': { id: 'browser.goto' } }
      })

      const result = await store.loadModules('en')

      expect(result).toEqual({ ok: true })
      expect(store.defaultModulesList).toEqual([])
      expect(store.expertModulesList).toEqual([])
      expect(store.availableSteps).toEqual({})
      expect(store.moduleCategories).toEqual([])
      expect(store.modulesMetadata).toEqual({ 'browser.goto': { id: 'browser.goto' } })
      expect(store.hasModules).toBe(true)
    })

    it('saves to localStorage cache', async () => {
      getTieredCatalog.mockResolvedValue(mockResponse)

      await store.loadModules('en')

      expect(localStorageMock.setItem).toHaveBeenCalled()
      const cacheCall = localStorageMock.setItem.mock.calls[0]
      expect(cacheCall[0]).toBe('flyto_modules_cache')
      const cached = JSON.parse(cacheCall[1])
      expect(cached.locale).toBe('en')
      expect(cached.defaultModules).toEqual([{ id: 'mod-1' }])
    })

    it('returns error result on API failure', async () => {
      getTieredCatalog.mockRejectedValue(new Error('API down'))

      const result = await store.loadModules('en')

      expect(result).toEqual({ ok: false, error: 'API down' })
      expect(store.error).toBe('API down')
      expect(store.isLoading).toBe(false)
      expect(store.hasLoaded).toBe(false)
      expect(store.isReady).toBe(false)
    })

    it('does not double-fetch when already loading', async () => {
      store.isLoading = true

      const result = await store.loadModules('en')

      expect(result).toEqual({ ok: true })
      expect(getTieredCatalog).not.toHaveBeenCalled()
    })

    it('uses cache when available and valid', async () => {
      // Build a cache with enough metadata entries (>= 50)
      const metadata = {}
      for (let i = 0; i < 60; i++) metadata[`mod-${i}`] = { id: `mod-${i}` }

      const cacheData = {
        locale: 'en',
        timestamp: Date.now(),
        version: '1.0',
        defaultModules: [{ id: 'mod-0' }],
        expertModules: [],
        modulesByCategory: {},
        moduleCategories: ['cat'],
        modulesMetadata: metadata
      }
      localStorageMock.getItem.mockReturnValue(JSON.stringify(cacheData))

      const result = await store.loadModules('en')

      expect(result).toEqual({ ok: true, fromCache: true })
      expect(getTieredCatalog).not.toHaveBeenCalled()
      expect(Object.keys(store.modulesMetadata).length).toBe(60)
      expect(store.hasLoaded).toBe(true)
      expect(store.isReady).toBe(true)
    })

    it('ignores stale cache (different locale)', async () => {
      const metadata = {}
      for (let i = 0; i < 60; i++) metadata[`mod-${i}`] = { id: `mod-${i}` }

      localStorageMock.getItem.mockReturnValue(JSON.stringify({
        locale: 'zh',
        timestamp: Date.now(),
        defaultModules: [{ id: 'mod-0' }],
        modulesMetadata: metadata
      }))

      getTieredCatalog.mockResolvedValue(mockResponse)

      await store.loadModules('en')

      expect(getTieredCatalog).toHaveBeenCalled()
    })

    it('bypasses cache when forceRefresh is true', async () => {
      const metadata = {}
      for (let i = 0; i < 60; i++) metadata[`mod-${i}`] = { id: `mod-${i}` }

      localStorageMock.getItem.mockReturnValue(JSON.stringify({
        locale: 'en',
        timestamp: Date.now(),
        defaultModules: [{ id: 'mod-0' }],
        modulesMetadata: metadata
      }))

      getTieredCatalog.mockResolvedValue(mockResponse)

      await store.loadModules('en', { forceRefresh: true })

      expect(getTieredCatalog).toHaveBeenCalled()
    })

    it('passes excludeTemplateId to API', async () => {
      getTieredCatalog.mockResolvedValue(mockResponse)

      await store.loadModules('en', { excludeTemplateId: 'tmpl-1', forceRefresh: true })

      expect(getTieredCatalog).toHaveBeenCalledWith(expect.objectContaining({
        excludeTemplateId: 'tmpl-1'
      }))
    })

    it('extracts language base from locale string', async () => {
      getTieredCatalog.mockResolvedValue(mockResponse)

      await store.loadModules('zh-TW', { forceRefresh: true })

      expect(getTieredCatalog).toHaveBeenCalledWith(expect.objectContaining({
        lang: 'zh'
      }))
    })
  })

  // ==========================================================================
  // clearCache & reset
  // ==========================================================================
  describe('clearCache', () => {
    it('removes cache from localStorage', () => {
      store.clearCache()
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('flyto_modules_cache')
    })
  })

  describe('reset', () => {
    it('resets all state', () => {
      store.availableSteps = { cat: [{ id: 'mod-1' }] }
      store.modulesMetadata = { 'mod-1': {} }
      store.error = 'some error'
      store.hasLoaded = true

      store.reset()

      expect(store.availableSteps).toEqual({})
      expect(store.moduleCategories).toEqual([])
      expect(store.modulesMetadata).toEqual({})
      expect(store.defaultModulesList).toEqual([])
      expect(store.expertModulesList).toEqual([])
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.hasLoaded).toBe(false)
      expect(store.isReady).toBe(false)
    })
  })
})
