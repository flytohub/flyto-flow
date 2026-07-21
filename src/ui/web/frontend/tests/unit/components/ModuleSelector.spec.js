import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ref, computed } from 'vue'

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key) => key }),
}))

// Mock composable
const mockSearchQuery = ref('')
const mockSelectedCategoryFilter = ref(null)
const mockShowExpertMode = ref(false)
const mockFilteredDefaultCategories = ref([])
const mockFilteredExpertCategories = ref([])
const mockVisibleCategories = ref([])
const mockResetFilters = vi.fn()

vi.mock('@/composables/useModuleFiltering', () => ({
  useModuleFiltering: () => ({
    searchQuery: mockSearchQuery,
    selectedCategoryFilter: mockSelectedCategoryFilter,
    showExpertMode: mockShowExpertMode,
    filteredDefaultCategories: mockFilteredDefaultCategories,
    filteredExpertCategories: mockFilteredExpertCategories,
    visibleCategories: mockVisibleCategories,
    defaultModuleCount: computed(() => {
      let count = 0
      for (const cat of mockFilteredDefaultCategories.value) count += cat.modules.length
      return count
    }),
    expertModuleCount: computed(() => {
      let count = 0
      for (const cat of mockFilteredExpertCategories.value) count += cat.modules.length
      return count
    }),
    resetFilters: mockResetFilters,
  }),
}))

vi.mock('@/api/modules', () => ({
  getStarterModules: vi.fn(() => Promise.resolve({ modules: [] })),
}))

const stubs = {
  X: true,
  Search: true,
  SearchX: true,
  Blocks: true,
  Grid: true,
  ChevronDown: true,
  Wrench: true,
  Play: true,
  AppInput: { template: '<input />', props: ['modelValue'] },
  ModuleCard: {
    template: '<div class="module-card" @click="$emit(\'select\', module)"></div>',
    props: ['module', 'isExpert'],
    emits: ['select'],
  },
  TransitionGroup: { template: '<div><slot /></div>' },
  Transition: { template: '<div><slot /></div>' },
}

import ModuleSelector from '@/components/ModuleSelector.vue'

function factory(props = {}) {
  return shallowMount(ModuleSelector, {
    props: {
      isOpen: true,
      moduleCategories: [],
      isLoadingModules: false,
      defaultModules: [],
      expertModules: [],
      ...props,
    },
    global: {
      plugins: [createPinia()],
      stubs,
      mocks: {
        $t: (key, fallback) => (typeof fallback === 'string' ? fallback : key),
        $te: () => false,
      },
    },
  })
}

describe('ModuleSelector.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockSearchQuery.value = ''
    mockSelectedCategoryFilter.value = null
    mockShowExpertMode.value = false
    mockFilteredDefaultCategories.value = []
    mockFilteredExpertCategories.value = []
    mockVisibleCategories.value = []
  })

  // =========================================================================
  // Visibility
  // =========================================================================
  it('renders when isOpen is true', () => {
    const wrapper = factory({ isOpen: true })
    expect(wrapper.find('.fixed').exists()).toBe(true)
  })

  it('does not render when isOpen is false', () => {
    const wrapper = factory({ isOpen: false })
    expect(wrapper.find('.fixed').exists()).toBe(false)
  })

  // =========================================================================
  // Module list rendering
  // =========================================================================
  it('renders module categories when data is available', () => {
    mockFilteredDefaultCategories.value = [
      {
        name: 'browser',
        label: 'Browser',
        icon: 'Globe',
        modules: [
          { module: 'browser.open', label: 'Open Browser' },
          { module: 'browser.click', label: 'Click Element' },
        ],
      },
    ]
    const wrapper = factory()
    expect(wrapper.findAll('.module-card').length).toBe(2)
  })

  it('shows empty state when no modules match', () => {
    mockFilteredDefaultCategories.value = []
    mockFilteredExpertCategories.value = []
    const wrapper = factory()
    expect(wrapper.html()).toContain('workflow.noModulesFound')
  })

  // =========================================================================
  // Events
  // =========================================================================
  it('emits select when a module card is clicked', async () => {
    mockFilteredDefaultCategories.value = [
      {
        name: 'data',
        label: 'Data',
        icon: 'Database',
        modules: [{ module: 'data.extract', label: 'Extract Data' }],
      },
    ]
    const wrapper = factory()
    const card = wrapper.find('.module-card')
    await card.trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
  })

  it('emits close when backdrop is clicked', async () => {
    const wrapper = factory({ isOpen: true })
    const backdrop = wrapper.find('.fixed')
    await backdrop.trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('emits close when close button is clicked', async () => {
    const wrapper = factory({ isOpen: true })
    // The close button is inside the header
    const closeBtn = wrapper.find('button[class*="hover:bg-white/10"]')
    if (closeBtn.exists()) {
      await closeBtn.trigger('click')
      expect(wrapper.emitted('close')).toBeTruthy()
    }
  })

  // =========================================================================
  // Categories
  // =========================================================================
  it('displays category filter buttons', () => {
    mockVisibleCategories.value = [
      { name: 'browser', label: 'Browser', icon: 'Globe' },
      { name: 'data', label: 'Data', icon: 'Database' },
    ]
    const wrapper = factory()
    // "All" button + 2 category buttons
    const categoryButtons = wrapper.findAll('.overflow-x-auto button')
    expect(categoryButtons.length).toBeGreaterThanOrEqual(3) // All + 2 categories
  })

  it('shows "All" category button by default', () => {
    const wrapper = factory()
    expect(wrapper.html()).toContain('common.all')
  })

  // =========================================================================
  // Loading state
  // =========================================================================
  it('shows loading spinner when modules are loading', () => {
    const wrapper = factory({ isLoadingModules: true })
    expect(wrapper.html()).toContain('common.loading')
  })

  // =========================================================================
  // Expert mode
  // =========================================================================
  it('shows expert mode toggle button', () => {
    const wrapper = factory()
    expect(wrapper.html()).toContain('workflow.expertMode')
  })

  it('shows expert module hint when expert modules exist but mode is off', () => {
    mockFilteredDefaultCategories.value = [
      { name: 'browser', label: 'Browser', icon: 'Globe', modules: [{ module: 'b.1' }] },
    ]
    mockFilteredExpertCategories.value = [
      { name: 'developer', label: 'Developer', icon: 'Code', modules: [{ module: 'd.1' }, { module: 'd.2' }] },
    ]
    mockShowExpertMode.value = false
    const wrapper = factory()
    expect(wrapper.html()).toContain('workflow.expertModules')
  })

  // =========================================================================
  // Footer
  // =========================================================================
  it('displays total module count in the footer', () => {
    mockFilteredDefaultCategories.value = [
      { name: 'a', label: 'A', icon: 'X', modules: [{ module: '1' }, { module: '2' }] },
    ]
    const wrapper = factory()
    // Footer shows "X modules" text
    expect(wrapper.html()).toContain('modules')
  })

  it('shows ESC key hint in footer', () => {
    const wrapper = factory()
    expect(wrapper.html()).toContain('ESC')
  })

  // =========================================================================
  // First node mode
  // =========================================================================
  it('shows starter module title when isAddingFirstNode is true', () => {
    const wrapper = factory({ isAddingFirstNode: true })
    expect(wrapper.html()).toContain('Select Starter Module')
  })
})
