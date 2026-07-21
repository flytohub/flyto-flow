import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref, nextTick } from 'vue'
import {
  groupModulesByCategory,
  filterModulesByQuery,
  useModuleFiltering
} from '@/composables/useModuleFiltering'

describe('groupModulesByCategory', () => {
  it('returns empty array for empty input', () => {
    expect(groupModulesByCategory([])).toEqual([])
  })

  it('groups modules by category field', () => {
    const modules = [
      { category: 'browser', label: 'Click' },
      { category: 'browser', label: 'Navigate' },
      { category: 'api', label: 'HTTP Request' }
    ]
    const groups = groupModulesByCategory(modules)
    expect(groups).toHaveLength(2)
    const browserGroup = groups.find(g => g.name === 'browser')
    expect(browserGroup.modules).toHaveLength(2)
    expect(browserGroup.label).toBe('Browser')
  })

  it('falls back to categoryName field', () => {
    const modules = [{ categoryName: 'data', label: 'Parse' }]
    const groups = groupModulesByCategory(modules)
    expect(groups[0].name).toBe('data')
  })

  it('defaults to "other" when no category', () => {
    const modules = [{ label: 'Unknown' }]
    const groups = groupModulesByCategory(modules)
    expect(groups[0].name).toBe('other')
  })

  it('uses categoryIcon or icon for group icon', () => {
    const modules = [{ category: 'test', categoryIcon: 'MyIcon' }]
    const groups = groupModulesByCategory(modules)
    expect(groups[0].icon).toBe('MyIcon')
  })
})

describe('filterModulesByQuery', () => {
  const modules = [
    { label: 'Click Element', description: 'Click on page', module: 'browser.click', tags: ['ui'] },
    { label: 'HTTP Request', description: 'Make API call', module: 'api.http', tags: ['network'] },
    { label: 'Navigate URL', description: 'Go to page', moduleId: 'browser.navigate', tags: [] }
  ]

  it('returns all modules when query is empty', () => {
    expect(filterModulesByQuery(modules, '')).toEqual(modules)
    expect(filterModulesByQuery(modules, null)).toEqual(modules)
  })

  it('filters by label', () => {
    const result = filterModulesByQuery(modules, 'click')
    expect(result).toHaveLength(1)
    expect(result[0].label).toBe('Click Element')
  })

  it('filters by description', () => {
    const result = filterModulesByQuery(modules, 'API call')
    expect(result).toHaveLength(1)
    expect(result[0].label).toBe('HTTP Request')
  })

  it('filters by module field', () => {
    const result = filterModulesByQuery(modules, 'browser.click')
    expect(result).toHaveLength(1)
  })

  it('filters by moduleId field', () => {
    const result = filterModulesByQuery(modules, 'browser.navigate')
    expect(result).toHaveLength(1)
  })

  it('filters by tags', () => {
    const result = filterModulesByQuery(modules, 'network')
    expect(result).toHaveLength(1)
    expect(result[0].label).toBe('HTTP Request')
  })

  it('is case-insensitive', () => {
    expect(filterModulesByQuery(modules, 'CLICK')).toHaveLength(1)
    expect(filterModulesByQuery(modules, 'HTTP')).toHaveLength(1)
  })
})

describe('useModuleFiltering', () => {
  let defaultModules, expertModules

  beforeEach(() => {
    defaultModules = ref([
      { category: 'browser', label: 'Click', description: '' },
      { category: 'browser', label: 'Navigate', description: '' },
      { category: 'api', label: 'HTTP', description: '' }
    ])
    expertModules = ref([
      { category: 'scraper', label: 'Extract Data', description: '' }
    ])
  })

  it('returns expected API', () => {
    const result = useModuleFiltering({ defaultModules, expertModules })
    expect(result.searchQuery).toBeDefined()
    expect(result.selectedCategoryFilter).toBeDefined()
    expect(result.showExpertMode).toBeDefined()
    expect(result.filteredDefaultCategories).toBeDefined()
    expect(result.filteredExpertCategories).toBeDefined()
    expect(result.defaultModuleCount).toBeDefined()
    expect(result.expertModuleCount).toBeDefined()
    expect(result.resetFilters).toBeDefined()
  })

  it('groups default modules into categories', () => {
    const { defaultModulesGrouped } = useModuleFiltering({ defaultModules, expertModules })
    expect(defaultModulesGrouped.value).toHaveLength(2) // browser, api
  })

  it('filters by search query', async () => {
    const { searchQuery, filteredDefaultCategories } = useModuleFiltering({ defaultModules, expertModules })
    searchQuery.value = 'Click'
    await nextTick()
    const totalModules = filteredDefaultCategories.value.reduce((sum, cat) => sum + cat.modules.length, 0)
    expect(totalModules).toBe(1)
  })

  it('filters by selected category', async () => {
    const { selectedCategoryFilter, filteredDefaultCategories } = useModuleFiltering({ defaultModules, expertModules })
    selectedCategoryFilter.value = 'api'
    await nextTick()
    expect(filteredDefaultCategories.value).toHaveLength(1)
    expect(filteredDefaultCategories.value[0].name).toBe('api')
  })

  it('counts modules correctly', () => {
    const { defaultModuleCount, expertModuleCount } = useModuleFiltering({ defaultModules, expertModules })
    expect(defaultModuleCount.value).toBe(3)
    expect(expertModuleCount.value).toBe(1)
  })

  it('resetFilters clears search and category filter', async () => {
    const { searchQuery, selectedCategoryFilter, resetFilters } = useModuleFiltering({ defaultModules, expertModules })
    searchQuery.value = 'test'
    selectedCategoryFilter.value = 'browser'
    resetFilters()
    expect(searchQuery.value).toBe('')
    expect(selectedCategoryFilter.value).toBeNull()
  })

  it('auto-enables expert mode when no default modules exist', async () => {
    const emptyDefault = ref([])
    const { showExpertMode } = useModuleFiltering({ defaultModules: emptyDefault, expertModules })
    await nextTick()
    expect(showExpertMode.value).toBe(true)
  })

  it('visibleCategories includes expert categories when expert mode is on', async () => {
    const { showExpertMode, visibleCategories } = useModuleFiltering({ defaultModules, expertModules })
    showExpertMode.value = true
    await nextTick()
    const names = visibleCategories.value.map(c => c.name)
    expect(names).toContain('scraper')
  })

  it('visibleCategories excludes expert categories when expert mode is off', () => {
    const { showExpertMode, visibleCategories } = useModuleFiltering({ defaultModules, expertModules })
    showExpertMode.value = false
    const names = visibleCategories.value.map(c => c.name)
    expect(names).not.toContain('scraper')
  })
})
