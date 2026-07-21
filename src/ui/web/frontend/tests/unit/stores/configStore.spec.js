import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/platform', () => ({
  getAllConfig: vi.fn()
}))

import { useConfigStore } from '@/stores/config/configStoreCore'
import { DEFAULTS } from '@/stores/config/defaults'
import { getAllConfig } from '@/api/platform'

describe('useConfigStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useConfigStore()
    vi.clearAllMocks()
  })

  // ==========================================================================
  // Initial State (defaults)
  // ==========================================================================
  describe('initial state', () => {
    it('initializes with DEFAULTS', () => {
      expect(store.timing).toEqual(DEFAULTS.timing)
      expect(store.layout).toEqual(DEFAULTS.layout)
      expect(store.theme).toEqual(DEFAULTS.theme)
      expect(store.limits).toEqual(DEFAULTS.limits)
      expect(store.isLoaded).toBe(false)
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  // ==========================================================================
  // Computed Getters (shortcuts)
  // ==========================================================================
  describe('computed getters', () => {
    it('pollingInterval returns default polling value', () => {
      expect(store.pollingInterval).toBe(2000)
    })

    it('executionPollingInterval returns execution polling value', () => {
      expect(store.executionPollingInterval).toBe(1000)
    })

    it('notificationDuration returns success duration', () => {
      expect(store.notificationDuration).toBe(3000)
    })

    it('debounceDelay returns search debounce', () => {
      expect(store.debounceDelay).toBe(300)
    })

    it('nodeSpacing returns horizontal and vertical', () => {
      expect(store.nodeSpacing).toEqual({ horizontal: 320, vertical: 150 })
    })

    it('initialPosition returns x and y', () => {
      expect(store.initialPosition).toEqual({ x: 200, y: 100 })
    })

    it('maxFileSize returns file limit', () => {
      expect(store.maxFileSize).toBe(10485760)
    })

    it('pageSize returns pagination default', () => {
      expect(store.pageSize).toBe(20)
    })

    it('defaultLLMProvider returns openai', () => {
      expect(store.defaultLLMProvider).toBe('openai')
    })

    it('defaultLLMModel returns gpt-4o', () => {
      expect(store.defaultLLMModel).toBe('gpt-4o')
    })

    it('defaultTriggerType returns manual', () => {
      expect(store.defaultTriggerType).toBe('manual')
    })

    it('statusColors returns theme status colors', () => {
      expect(store.statusColors.running).toBe('#3b82f6')
      expect(store.statusColors.success).toBe('#10b981')
    })
  })

  // ==========================================================================
  // loadConfig
  // ==========================================================================
  describe('loadConfig', () => {
    it('loads config from backend and updates state', async () => {
      const backendConfig = {
        timing: { ...DEFAULTS.timing, polling: { ...DEFAULTS.timing.polling, default: 5000 } },
        layout: DEFAULTS.layout,
        theme: DEFAULTS.theme,
        limits: { ...DEFAULTS.limits, pagination: { defaultPageSize: 50 } },
        shortcuts: DEFAULTS.shortcuts,
        llm: { providers: [{ id: 'openai', models: ['gpt-4o'] }], defaults: { provider: 'openai', model: 'gpt-4o' } },
        triggers: DEFAULTS.triggers,
        http: DEFAULTS.http,
        paramTypes: {},
        outputTypes: {},
        marketplace: DEFAULTS.marketplace,
        subscription: DEFAULTS.subscription,
        workflowTypes: DEFAULTS.workflowTypes,
        formTypes: DEFAULTS.formTypes,
        countries: ['US', 'TW'],
        quickStart: DEFAULTS.quickStart,
        messaging: DEFAULTS.messaging,
        breakpoints: DEFAULTS.breakpoints,
        nodeDesign: DEFAULTS.nodeDesign,
      }
      getAllConfig.mockResolvedValue(backendConfig)

      await store.loadConfig()

      expect(store.isLoaded).toBe(true)
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.pollingInterval).toBe(5000)
      expect(store.pageSize).toBe(50)
      expect(store.countries).toEqual(['US', 'TW'])
    })

    it('does not reload when already loaded', async () => {
      store.isLoaded = true

      await store.loadConfig()

      expect(getAllConfig).not.toHaveBeenCalled()
    })

    it('does not reload when currently loading', async () => {
      store.isLoading = true

      await store.loadConfig()

      expect(getAllConfig).not.toHaveBeenCalled()
    })

    it('force refreshes even when loaded', async () => {
      store.isLoaded = true
      getAllConfig.mockResolvedValue({})

      await store.loadConfig(true)

      expect(getAllConfig).toHaveBeenCalledWith({ forceRefresh: true })
    })

    it('sets error on failure', async () => {
      getAllConfig.mockRejectedValue(new Error('Network timeout'))

      await store.loadConfig()

      expect(store.error).toBe('Network timeout')
      expect(store.isLoading).toBe(false)
      expect(store.isLoaded).toBe(false)
    })

    it('falls back to DEFAULTS for missing backend values', async () => {
      getAllConfig.mockResolvedValue({})

      await store.loadConfig()

      expect(store.timing).toEqual(DEFAULTS.timing)
      expect(store.layout).toEqual(DEFAULTS.layout)
      expect(store.theme).toEqual(DEFAULTS.theme)
    })
  })

  // ==========================================================================
  // Config Getter Functions
  // ==========================================================================
  describe('getTiming', () => {
    it('returns specific timing value', () => {
      expect(store.getTiming('polling', 'executionStatus')).toBe(1000)
    })

    it('returns fallback for missing key', () => {
      expect(store.getTiming('polling', 'nonexistent', 9999)).toBe(9999)
    })

    it('returns default fallback of 1000', () => {
      expect(store.getTiming('nonexistent', 'nonexistent')).toBe(1000)
    })
  })

  describe('getLayout', () => {
    it('returns specific layout value', () => {
      expect(store.getLayout('workflow', 'horizontalSpacing')).toBe(320)
    })

    it('returns fallback for missing key', () => {
      expect(store.getLayout('workflow', 'missing', 100)).toBe(100)
    })
  })

  describe('getColor', () => {
    it('returns specific color', () => {
      expect(store.getColor('colors', 'primary')).toBe('#3b82f6')
    })

    it('returns fallback for missing key', () => {
      expect(store.getColor('colors', 'missing', '#000')).toBe('#000')
    })
  })

  describe('getLimit', () => {
    it('returns specific limit', () => {
      expect(store.getLimit('logs', 'maxEntries')).toBe(1000)
    })
  })

  describe('getShortcut', () => {
    it('returns specific shortcut', () => {
      expect(store.getShortcut('workflow', 'save')).toBe('Ctrl+S')
    })

    it('returns fallback for missing shortcut', () => {
      expect(store.getShortcut('workflow', 'missing', 'N/A')).toBe('N/A')
    })
  })

  // ==========================================================================
  // LLM Helpers
  // ==========================================================================
  describe('LLM helpers', () => {
    it('getLLMProviders returns empty by default', () => {
      expect(store.getLLMProviders()).toEqual([])
    })

    it('getLLMModels returns empty for unknown provider', () => {
      expect(store.getLLMModels('unknown')).toEqual([])
    })

    it('getLLMModels returns models for known provider', () => {
      store.llm = {
        providers: [{ id: 'openai', models: ['gpt-4o', 'gpt-3.5'] }],
        defaults: {}
      }
      expect(store.getLLMModels('openai')).toEqual(['gpt-4o', 'gpt-3.5'])
    })

    it('getLLMDefaults returns defaults', () => {
      const defaults = store.getLLMDefaults()
      expect(defaults.provider).toBe('openai')
      expect(defaults.model).toBe('gpt-4o')
    })
  })

  // ==========================================================================
  // HTTP, Trigger, Marketplace Helpers
  // ==========================================================================
  describe('HTTP helpers', () => {
    it('returns empty arrays by default', () => {
      expect(store.getHTTPMethods()).toEqual([])
      expect(store.getHTTPAuthTypes()).toEqual([])
      expect(store.getHTTPBodyTypes()).toEqual([])
    })
  })

  describe('getTriggerTypes', () => {
    it('returns empty by default', () => {
      expect(store.getTriggerTypes()).toEqual([])
    })
  })

  describe('marketplace helpers', () => {
    it('returns empty arrays by default', () => {
      expect(store.getMarketplaceCategories()).toEqual([])
      expect(store.getCurrencies()).toEqual([])
      expect(store.getVisibilityOptions()).toEqual([])
    })
  })

  // ==========================================================================
  // Workflow & Form Type Helpers
  // ==========================================================================
  describe('workflow type helpers', () => {
    it('returns empty arrays by default', () => {
      expect(store.getNodeTypes()).toEqual([])
      expect(store.getEdgeTypes()).toEqual([])
    })
  })

  describe('form type helpers', () => {
    it('returns empty arrays by default', () => {
      expect(store.getFormFieldTypes()).toEqual([])
      expect(store.getInputTypes()).toEqual([])
      expect(store.getOutputTypes()).toEqual([])
      expect(store.getBindingSources()).toEqual([])
    })
  })

  // ==========================================================================
  // Misc Helpers
  // ==========================================================================
  describe('misc helpers', () => {
    it('getCountries returns empty by default', () => {
      expect(store.getCountries()).toEqual([])
    })

    it('getQuickStartModules returns empty by default', () => {
      expect(store.getQuickStartModules()).toEqual([])
    })

    it('getMessagingProviders returns empty by default', () => {
      expect(store.getMessagingProviders()).toEqual([])
    })

    it('getBreakpointTypes returns empty by default', () => {
      expect(store.getBreakpointTypes()).toEqual([])
    })

    it('getSubscriptionPlans returns empty by default', () => {
      expect(store.getSubscriptionPlans()).toEqual([])
    })
  })

  // ==========================================================================
  // Node Design
  // ==========================================================================
  describe('getNodeDimensions', () => {
    it('returns dimensions for known node type', () => {
      const dims = store.getNodeDimensions('branch')
      expect(dims).toEqual({ shape: 'diamond', width: 76, height: 76 })
    })

    it('returns default dimensions for unknown type', () => {
      const dims = store.getNodeDimensions('unknown_type')
      expect(dims).toEqual({ shape: 'rectangle', width: 240, height: 76 })
    })
  })

  // ==========================================================================
  // Reset
  // ==========================================================================
  describe('reset', () => {
    it('resets all state to defaults', async () => {
      getAllConfig.mockResolvedValue({
        timing: { polling: { default: 9999 } },
      })
      await store.loadConfig()

      store.reset()

      expect(store.timing).toEqual(DEFAULTS.timing)
      expect(store.isLoaded).toBe(false)
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
    })
  })
})
