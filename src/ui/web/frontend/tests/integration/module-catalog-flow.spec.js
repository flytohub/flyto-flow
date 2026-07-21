/**
 * Integration Test: Module Catalog Flow
 *
 * Tests real module loading and filtering through:
 * modulesStore -> useModuleFiltering composable -> modules API (mocked)
 *
 * Only the HTTP boundary is mocked. All store logic, composable
 * reactivity, computed properties, and filtering are real.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref, nextTick } from 'vue'

// Mock only the HTTP boundary
vi.mock('@/api/modules', () => ({
  getTieredCatalog: vi.fn(),
  getModule: vi.fn()
}))

// Mock telemetry
vi.mock('@/services/telemetry', () => ({
  telemetry: { track: vi.fn() }
}))

import { useModulesStore } from '@/stores/modulesStore'
import { useModuleFiltering, groupModulesByCategory, filterModulesByQuery } from '@/composables/useModuleFiltering'
import { getTieredCatalog } from '@/api/modules'

// Realistic module catalog fixture
const REALISTIC_CATALOG = {
  default: {
    modules: [
      { moduleId: 'browser.open', label: 'Open Browser', description: 'Opens a browser page', category: 'browser', tags: ['web', 'automation'] },
      { moduleId: 'browser.click', label: 'Click Element', description: 'Clicks a page element', category: 'browser', tags: ['web', 'interaction'] },
      { moduleId: 'browser.screenshot', label: 'Take Screenshot', description: 'Captures a screenshot', category: 'browser', tags: ['capture'] },
      { moduleId: 'data.csv_read', label: 'Read CSV', description: 'Reads CSV file', category: 'data', tags: ['file', 'csv'] },
      { moduleId: 'data.json_parse', label: 'Parse JSON', description: 'Parses JSON string', category: 'data', tags: ['json', 'parse'] },
      { moduleId: 'http.request', label: 'HTTP Request', description: 'Makes HTTP request', category: 'http', tags: ['api', 'rest'] },
      { moduleId: 'ai.llm', label: 'AI Chat', description: 'Chat with LLM', category: 'ai', tags: ['llm', 'openai'] },
    ]
  },
  expert: {
    modules: [
      { moduleId: 'browser.eval', label: 'Evaluate JS', description: 'Runs JavaScript in page', category: 'browser', tags: ['advanced', 'js'] },
      { moduleId: 'code.python', label: 'Python Code', description: 'Runs Python code', category: 'code', tags: ['python', 'script'] },
    ]
  },
  modulesByCategory: {
    browser: [
      { moduleId: 'browser.open', label: 'Open Browser' },
      { moduleId: 'browser.click', label: 'Click Element' },
      { moduleId: 'browser.screenshot', label: 'Take Screenshot' },
    ],
    data: [
      { moduleId: 'data.csv_read', label: 'Read CSV' },
      { moduleId: 'data.json_parse', label: 'Parse JSON' },
    ],
    http: [
      { moduleId: 'http.request', label: 'HTTP Request' },
    ],
    ai: [
      { moduleId: 'ai.llm', label: 'AI Chat' },
    ]
  },
  moduleCategories: ['browser', 'data', 'http', 'ai'],
  modulesMetadata: {
    'browser.open': { moduleId: 'browser.open', label: 'Open Browser', category: 'browser', tier: 'default' },
    'browser.click': { moduleId: 'browser.click', label: 'Click Element', category: 'browser', tier: 'default' },
    'browser.screenshot': { moduleId: 'browser.screenshot', label: 'Take Screenshot', category: 'browser', tier: 'default' },
    'data.csv_read': { moduleId: 'data.csv_read', label: 'Read CSV', category: 'data', tier: 'default' },
    'data.json_parse': { moduleId: 'data.json_parse', label: 'Parse JSON', category: 'data', tier: 'default' },
    'http.request': { moduleId: 'http.request', label: 'HTTP Request', category: 'http', tier: 'default' },
    'ai.llm': { moduleId: 'ai.llm', label: 'AI Chat', category: 'ai', tier: 'default' },
    'browser.eval': { moduleId: 'browser.eval', label: 'Evaluate JS', category: 'browser', tier: 'expert' },
    'code.python': { moduleId: 'code.python', label: 'Python Code', category: 'code', tier: 'expert' },
  },
  version: '2.6.0'
}

describe('Module Catalog Flow Integration', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useModulesStore()
    vi.clearAllMocks()
    // Clear localStorage cache
    localStorage.removeItem('flyto_modules_cache')
  })

  afterEach(() => {
    localStorage.removeItem('flyto_modules_cache')
  })

  // =========================================================================
  // Load catalog -> store hydration
  // =========================================================================

  describe('load catalog', () => {
    it('should load modules and hydrate all store fields', async () => {
      getTieredCatalog.mockResolvedValueOnce(REALISTIC_CATALOG)

      expect(store.hasModules).toBe(false)

      const result = await store.loadModules('en')

      expect(result.ok).toBe(true)
      expect(store.hasModules).toBe(true)
      expect(store.defaultModulesList).toHaveLength(7)
      expect(store.expertModulesList).toHaveLength(2)
      expect(store.moduleCategories).toEqual(['browser', 'data', 'http', 'ai'])
      expect(Object.keys(store.modulesMetadata)).toHaveLength(9)

      // Verify getModuleById computed
      const browserOpen = store.getModuleById('browser.open')
      expect(browserOpen).toBeDefined()
      expect(browserOpen.label).toBe('Open Browser')

      // Verify getModulesByCategory computed
      const browserModules = store.getModulesByCategory('browser')
      expect(browserModules).toHaveLength(3)
    })

    it('should handle API errors', async () => {
      getTieredCatalog.mockRejectedValueOnce(new Error('Server unavailable'))

      const result = await store.loadModules('en')

      expect(result.ok).toBe(false)
      expect(result.error).toBe('Server unavailable')
      expect(store.error).toBe('Server unavailable')
      expect(store.hasModules).toBe(false)
    })

    it('should prevent concurrent loads', async () => {
      getTieredCatalog.mockResolvedValueOnce(REALISTIC_CATALOG)

      store.isLoading = true
      const result = await store.loadModules('en')

      expect(result.ok).toBe(true)
      expect(getTieredCatalog).not.toHaveBeenCalled()
    })
  })

  // =========================================================================
  // Module filtering composable (real)
  // =========================================================================

  describe('useModuleFiltering composable', () => {
    it('should group modules by category', () => {
      const defaultModules = ref(REALISTIC_CATALOG.default.modules)
      const expertModules = ref(REALISTIC_CATALOG.expert.modules)

      const filtering = useModuleFiltering({ defaultModules, expertModules })

      // Verify real grouping
      const defaultGroups = filtering.defaultModulesGrouped.value
      expect(defaultGroups.length).toBeGreaterThan(0)

      const browserGroup = defaultGroups.find(g => g.name === 'browser')
      expect(browserGroup).toBeDefined()
      expect(browserGroup.modules).toHaveLength(3)
      expect(browserGroup.label).toBe('Browser') // capitalize first letter

      const dataGroup = defaultGroups.find(g => g.name === 'data')
      expect(dataGroup).toBeDefined()
      expect(dataGroup.modules).toHaveLength(2)
    })

    it('should filter by search query', async () => {
      const defaultModules = ref(REALISTIC_CATALOG.default.modules)
      const expertModules = ref(REALISTIC_CATALOG.expert.modules)

      const filtering = useModuleFiltering({ defaultModules, expertModules })

      // Search for "csv"
      filtering.searchQuery.value = 'csv'
      await nextTick()

      const filtered = filtering.filteredDefaultCategories.value
      const totalModules = filtered.reduce((sum, cat) => sum + cat.modules.length, 0)
      expect(totalModules).toBe(1)
      expect(filtered[0].modules[0].moduleId).toBe('data.csv_read')
    })

    it('should filter by category', async () => {
      const defaultModules = ref(REALISTIC_CATALOG.default.modules)
      const expertModules = ref(REALISTIC_CATALOG.expert.modules)

      const filtering = useModuleFiltering({ defaultModules, expertModules })

      filtering.selectedCategoryFilter.value = 'http'
      await nextTick()

      const filtered = filtering.filteredDefaultCategories.value
      expect(filtered).toHaveLength(1)
      expect(filtered[0].name).toBe('http')
      expect(filtered[0].modules[0].moduleId).toBe('http.request')
    })

    it('should combine search and category filter', async () => {
      const defaultModules = ref(REALISTIC_CATALOG.default.modules)
      const expertModules = ref(REALISTIC_CATALOG.expert.modules)

      const filtering = useModuleFiltering({ defaultModules, expertModules })

      filtering.selectedCategoryFilter.value = 'browser'
      filtering.searchQuery.value = 'screenshot'
      await nextTick()

      const filtered = filtering.filteredDefaultCategories.value
      expect(filtered).toHaveLength(1)
      expect(filtered[0].modules).toHaveLength(1)
      expect(filtered[0].modules[0].moduleId).toBe('browser.screenshot')
    })

    it('should compute module counts correctly', async () => {
      const defaultModules = ref(REALISTIC_CATALOG.default.modules)
      const expertModules = ref(REALISTIC_CATALOG.expert.modules)

      const filtering = useModuleFiltering({ defaultModules, expertModules })

      expect(filtering.defaultModuleCount.value).toBe(7)
      expect(filtering.expertModuleCount.value).toBe(2)

      // After search, count should update
      filtering.searchQuery.value = 'browser'
      await nextTick()

      // "browser" appears in labels/descriptions of browser modules
      expect(filtering.defaultModuleCount.value).toBeLessThan(7)
    })

    it('should auto-enable expert mode when no default modules', async () => {
      const defaultModules = ref([])
      const expertModules = ref(REALISTIC_CATALOG.expert.modules)

      const filtering = useModuleFiltering({ defaultModules, expertModules })
      await nextTick()

      expect(filtering.showExpertMode.value).toBe(true)
    })

    it('should reset filters', async () => {
      const defaultModules = ref(REALISTIC_CATALOG.default.modules)
      const expertModules = ref([])

      const filtering = useModuleFiltering({ defaultModules, expertModules })

      filtering.searchQuery.value = 'test'
      filtering.selectedCategoryFilter.value = 'browser'

      filtering.resetFilters()

      expect(filtering.searchQuery.value).toBe('')
      expect(filtering.selectedCategoryFilter.value).toBeNull()
    })

    it('should filter by tags', async () => {
      const defaultModules = ref(REALISTIC_CATALOG.default.modules)
      const expertModules = ref([])

      const filtering = useModuleFiltering({ defaultModules, expertModules })

      filtering.searchQuery.value = 'openai'
      await nextTick()

      const filtered = filtering.filteredDefaultCategories.value
      const totalModules = filtered.reduce((sum, cat) => sum + cat.modules.length, 0)
      expect(totalModules).toBe(1)
      expect(filtered[0].modules[0].moduleId).toBe('ai.llm')
    })
  })

  // =========================================================================
  // Standalone utility functions
  // =========================================================================

  describe('groupModulesByCategory utility', () => {
    it('should group modules and capitalize labels', () => {
      const modules = [
        { moduleId: 'a', category: 'web' },
        { moduleId: 'b', category: 'web' },
        { moduleId: 'c', category: 'data' },
      ]

      const groups = groupModulesByCategory(modules)
      expect(groups).toHaveLength(2)

      const webGroup = groups.find(g => g.name === 'web')
      expect(webGroup.label).toBe('Web')
      expect(webGroup.modules).toHaveLength(2)
    })

    it('should use "other" for modules without category', () => {
      const modules = [{ moduleId: 'x' }]
      const groups = groupModulesByCategory(modules)
      expect(groups[0].name).toBe('other')
    })
  })

  describe('filterModulesByQuery utility', () => {
    it('should return all modules when query is empty', () => {
      const modules = [{ label: 'A' }, { label: 'B' }]
      expect(filterModulesByQuery(modules, '')).toHaveLength(2)
      expect(filterModulesByQuery(modules, null)).toHaveLength(2)
    })

    it('should search across label, description, module, moduleId, tags', () => {
      const modules = [
        { label: 'Open Browser', description: 'Opens a page', module: 'browser.open', moduleId: 'browser.open', tags: ['web'] },
        { label: 'Read CSV', description: 'Reads data', module: 'data.csv', moduleId: 'data.csv', tags: ['file'] },
      ]

      expect(filterModulesByQuery(modules, 'browser')).toHaveLength(1)
      expect(filterModulesByQuery(modules, 'data')).toHaveLength(1)
      expect(filterModulesByQuery(modules, 'file')).toHaveLength(1)
      expect(filterModulesByQuery(modules, 'opens')).toHaveLength(1)
    })

    it('should be case-insensitive', () => {
      const modules = [{ label: 'HTTP Request', tags: [] }]
      expect(filterModulesByQuery(modules, 'http')).toHaveLength(1)
      expect(filterModulesByQuery(modules, 'HTTP')).toHaveLength(1)
    })
  })

  // =========================================================================
  // Store -> Composable integration
  // =========================================================================

  describe('store + composable integration', () => {
    it('should use store refs as composable inputs and react to changes', async () => {
      getTieredCatalog.mockResolvedValueOnce(REALISTIC_CATALOG)

      await store.loadModules('en')

      // Use store refs directly with composable
      const filtering = useModuleFiltering({
        defaultModules: ref(store.defaultModulesList),
        expertModules: ref(store.expertModulesList)
      })

      expect(filtering.defaultModuleCount.value).toBe(7)

      // Search
      filtering.searchQuery.value = 'ai'
      await nextTick()

      const aiModules = filtering.filteredDefaultCategories.value
      const totalAI = aiModules.reduce((sum, cat) => sum + cat.modules.length, 0)
      expect(totalAI).toBeGreaterThanOrEqual(1)
    })
  })

  // =========================================================================
  // Cache behavior
  // =========================================================================

  describe('cache behavior', () => {
    it('should clear cache', () => {
      localStorage.setItem('flyto_modules_cache', JSON.stringify({ test: true }))
      store.clearCache()
      expect(localStorage.getItem('flyto_modules_cache')).toBeNull()
    })

    it('should reset store state', () => {
      store.modulesMetadata = { 'a': { id: 'a' } }
      store.defaultModulesList = [{ id: 'a' }]
      store.error = 'some error'

      store.reset()

      expect(store.modulesMetadata).toEqual({})
      expect(store.defaultModulesList).toEqual([])
      expect(store.expertModulesList).toEqual([])
      expect(store.hasModules).toBe(false)
      expect(store.error).toBeNull()
    })
  })
})
