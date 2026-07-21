/**
 * Integration Test: Config & Capabilities Flow
 *
 * Tests real capabilities and config store flow:
 * capabilitiesStore -> capabilitiesAPI -> HTTP (mocked)
 * configStore -> platform API -> HTTP (mocked)
 *
 * Only the HTTP boundary is mocked. All computed properties,
 * feature flags, and derived state are real.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

// Mock only the HTTP boundary
vi.mock('@/api/capabilities', () => ({
  capabilitiesAPI: {
    getCapabilities: vi.fn(),
    reloadCapabilities: vi.fn()
  },
  getCapabilities: vi.fn(),
  reloadCapabilities: vi.fn(),
  default: {
    getCapabilities: vi.fn(),
    reloadCapabilities: vi.fn()
  }
}))

vi.mock('@/api/platform', () => ({
  getAllConfig: vi.fn()
}))

import { useCapabilitiesStore } from '@/stores/capabilitiesStore'
import { useConfigStore } from '@/stores/configStore'
import { capabilitiesAPI } from '@/api/capabilities'
import { getAllConfig } from '@/api/platform'
import {
  createCapabilityCheckers,
  DEFAULT_CAPABILITIES,
  DEFAULT_FEATURES,
  DEFAULT_UI
} from '@/stores/capabilities/featureFlagHelpers'

// Realistic capabilities response
const CLOUD_CAPABILITIES_RESPONSE = {
  deploymentMode: 'saas_cloud',
  licenseType: 'subscription',
  isLicensed: true,
  isPro: true,
  isAdmin: false,
  capabilities: [
    'auth.firebase',
    'core.workflow_run',
    'core.template_builder',
    'core.execution_history',
    'core.basic_logging',
    'core.execution_record_full',
    'local.metrics',
    'local.tracing',
    'local.alerts',
    'execution.replay',
    'execution.rerun',
    'execution.debug',
    'execution.evidence',
    'execution.lineage'
  ],
  features: {
    marketplace: true,
    billing: true,
    rbac: false,
    audit: true,
    sso: false,
    runners: false,
    vault: false,
    approvals: false,
    selfSignup: true,
    organization: true,
    observability: true,
    versioning: true,
    subscriptions: true
  },
  pages: {
    '/marketplace': true,
    '/admin/rbac': false,
    '/admin/audit': true,
    '/settings/organization': true,
    '/settings/billing': true
  },
  ui: {
    showMarketplace: true,
    showBilling: true,
    showOrgSettings: true,
    showAudit: true,
    showRbacSettings: false,
    showObservability: true,
    showVersioning: true,
    showSsoSettings: false,
    showSubscriptions: true,
    allowSelfSignup: true,
    authMethod: 'firebase',
    canUpgrade: false,
    upgradeUrl: '/pricing',
    upgradeFeatures: ['priority_support', 'advanced_analytics']
  },
  trialState: 'active',
  trialExpiresAt: '2026-02-15T00:00:00Z',
  trialDaysRemaining: 14
}

const LOCAL_OFFLINE_RESPONSE = {
  deploymentMode: 'local_offline',
  licenseType: 'free',
  isLicensed: false,
  isPro: false,
  isAdmin: false,
  capabilities: [
    'core.workflow_run',
    'core.template_builder',
    'core.execution_history',
    'core.basic_logging'
  ],
  features: {
    marketplace: false,
    billing: false,
    selfSignup: true
  },
  pages: {},
  ui: {
    showMarketplace: false,
    showBilling: false,
    canUpgrade: true,
    upgradeUrl: '/pricing'
  },
  trialState: null
}

describe('Config & Capabilities Flow Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // =========================================================================
  // Capabilities Store: Cloud deployment
  // =========================================================================

  describe('capabilities store - cloud deployment', () => {
    it('should load and hydrate all fields from API response', async () => {
      capabilitiesAPI.getCapabilities.mockResolvedValueOnce(CLOUD_CAPABILITIES_RESPONSE)

      const store = useCapabilitiesStore()
      await store.load()

      // Deployment mode
      expect(store.deploymentMode).toBe('saas_cloud')
      expect(store.isCloud).toBe(true)
      expect(store.isLocalOffline).toBe(false)
      expect(store.isEnterprise).toBe(false)

      // License
      expect(store.licenseType).toBe('subscription')
      expect(store.isLicensed).toBe(true)
      expect(store.isFree).toBe(false)
      expect(store.isSubscription).toBe(true)
      expect(store.isPro).toBe(true)
      expect(store.isAdmin).toBe(false)

      // Capabilities
      expect(store.capabilities).toHaveLength(14)
      expect(store.hasMetrics).toBe(true)
      expect(store.hasTracing).toBe(true)
      expect(store.hasAlerts).toBe(true)
      expect(store.hasExecutionReplay).toBe(true)
      expect(store.hasExecutionRerun).toBe(true)
      expect(store.hasExecutionDebug).toBe(true)
      expect(store.hasExecutionRecordFull).toBe(true)

      // Feature flags
      expect(store.hasMarketplace).toBe(true)
      expect(store.hasBilling).toBe(true)
      expect(store.hasRbac).toBe(false)
      expect(store.hasAudit).toBe(true)
      expect(store.hasSso).toBe(false)
      expect(store.hasOrganization).toBe(true)
      expect(store.hasObservability).toBe(true)
      expect(store.hasVersioning).toBe(true)
      expect(store.hasSubscriptions).toBe(true)

      // UI visibility
      expect(store.showMarketplace).toBe(true)
      expect(store.showBilling).toBe(true)
      expect(store.showOrgSettings).toBe(true)
      expect(store.showAuditLog).toBe(true)
      expect(store.showRbacSettings).toBe(false)
      expect(store.showObservability).toBe(true)
      expect(store.showSubscriptions).toBe(true)
      expect(store.allowSelfSignup).toBe(true)
      expect(store.authMethod).toBe('firebase')
      expect(store.canUpgrade).toBe(false)
      expect(store.upgradeFeatures).toEqual(['priority_support', 'advanced_analytics'])

      // Trial
      expect(store.trialState).toBe('active')
      expect(store.isTrialActive).toBe(true)
      expect(store.isTrialExpired).toBe(false)
      expect(store.trialDaysRemaining).toBe(14)

      // Loading state
      expect(store.isLoaded).toBe(true)
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('should support capability checking functions', async () => {
      capabilitiesAPI.getCapabilities.mockResolvedValueOnce(CLOUD_CAPABILITIES_RESPONSE)

      const store = useCapabilitiesStore()
      await store.load()

      expect(store.hasCapability('core.workflow_run')).toBe(true)
      expect(store.hasCapability('nonexistent')).toBe(false)

      expect(store.hasAnyCapability('core.workflow_run', 'nonexistent')).toBe(true)
      expect(store.hasAnyCapability('a', 'b')).toBe(false)

      expect(store.hasAllCapabilities('core.workflow_run', 'core.template_builder')).toBe(true)
      expect(store.hasAllCapabilities('core.workflow_run', 'nonexistent')).toBe(false)
    })

    it('should check page access', async () => {
      capabilitiesAPI.getCapabilities.mockResolvedValueOnce(CLOUD_CAPABILITIES_RESPONSE)

      const store = useCapabilitiesStore()
      await store.load()

      expect(store.canAccessPage('/marketplace')).toBe(true)
      expect(store.getExplicitPageAccess('/marketplace')).toBe(true)
      expect(store.canAccessPage('/admin/rbac')).toBe(false)
      expect(store.getExplicitPageAccess('/admin/rbac')).toBe(false)
      expect(store.canAccessPage('/admin/audit')).toBe(true)
      expect(store.canAccessPage('/settings/billing')).toBe(true)
      expect(store.canAccessPage('/payment')).toBe(false)
      expect(store.getExplicitPageAccess('/payment')).toBeNull()
      expect(store.canAccessPage('/messages')).toBe(false)
      expect(store.canAccessPage('/admin')).toBe(false)
    })

    it('should expose explicit backend denies for public routes', async () => {
      capabilitiesAPI.getCapabilities.mockResolvedValueOnce({
        ...CLOUD_CAPABILITIES_RESPONSE,
        pages: {
          ...CLOUD_CAPABILITIES_RESPONSE.pages,
          '/marketplace': false
        }
      })

      const store = useCapabilitiesStore()
      await store.load()

      expect(store.getExplicitPageAccess('/marketplace')).toBe(false)
      expect(store.canAccessPage('/marketplace')).toBe(false)
    })
  })

  // =========================================================================
  // Capabilities Store: Local offline deployment
  // =========================================================================

  describe('capabilities store - local offline', () => {
    it('should load offline capabilities correctly', async () => {
      capabilitiesAPI.getCapabilities.mockResolvedValueOnce(LOCAL_OFFLINE_RESPONSE)

      const store = useCapabilitiesStore()
      await store.load()

      expect(store.isLocalOffline).toBe(true)
      expect(store.isCloud).toBe(false)
      expect(store.isFree).toBe(true)
      expect(store.isPro).toBe(false)
      expect(store.isAdmin).toBe(false)
      expect(store.hasMarketplace).toBe(false)
      expect(store.hasBilling).toBe(false)
      expect(store.showMarketplace).toBe(false)
      expect(store.canUpgrade).toBe(true)
      expect(store.trialState).toBeNull()
      expect(store.isTrialActive).toBe(false)
      expect(store.canAccessPage('/dashboard')).toBe(true)
      expect(store.canAccessPage('/templates/builder')).toBe(true)
      expect(store.canAccessPage('/payment')).toBe(false)
      expect(store.canAccessPage('/admin/rbac')).toBe(false)
      expect(store.canAccessPage('/plugins')).toBe(false)
    })
  })

  // =========================================================================
  // Capabilities Store: Error handling (fail closed)
  // =========================================================================

  describe('capabilities store - error handling', () => {
    it('should fail closed on API error (no Pro access)', async () => {
      capabilitiesAPI.getCapabilities.mockRejectedValueOnce(
        new Error('Network error')
      )

      const store = useCapabilitiesStore()
      await store.load()

      // Verify fail-closed behavior
      expect(store.isPro).toBe(false)
      expect(store.isAdmin).toBe(false)
      expect(store.deploymentMode).toBe('local_offline')
      expect(store.licenseType).toBe('free')
      expect(store.capabilities).toEqual(DEFAULT_CAPABILITIES)
      expect(store.features).toEqual(DEFAULT_FEATURES)
      expect(store.ui).toEqual(DEFAULT_UI)
      expect(store.isLoaded).toBe(true) // Still marked as loaded
      expect(store.error).toBe('Network error')
    })
  })

  // =========================================================================
  // Capabilities Store: Reload
  // =========================================================================

  describe('capabilities store - reload', () => {
    it('should reload by clearing loaded state first', async () => {
      capabilitiesAPI.getCapabilities
        .mockResolvedValueOnce(LOCAL_OFFLINE_RESPONSE)
        .mockResolvedValueOnce(CLOUD_CAPABILITIES_RESPONSE)

      const store = useCapabilitiesStore()

      // Initial load
      await store.load()
      expect(store.isPro).toBe(false)

      // Reload with new data (e.g., user upgraded)
      await store.reload()
      expect(store.isPro).toBe(true)
      expect(store.isCloud).toBe(true)
    })

    it('should not double-load', async () => {
      capabilitiesAPI.getCapabilities.mockResolvedValue(CLOUD_CAPABILITIES_RESPONSE)

      const store = useCapabilitiesStore()
      await store.load()
      await store.load() // second call should be no-op

      expect(capabilitiesAPI.getCapabilities).toHaveBeenCalledTimes(1)
    })
  })

  // =========================================================================
  // Features always available (no Pro gate)
  // =========================================================================

  describe('features always available', () => {
    it('should always return true for non-gated features', async () => {
      capabilitiesAPI.getCapabilities.mockResolvedValueOnce(LOCAL_OFFLINE_RESPONSE)

      const store = useCapabilitiesStore()
      await store.load()

      // These are always true regardless of Pro status
      expect(store.hasReplay).toBe(true)
      expect(store.hasTests).toBe(true)
      expect(store.hasVersions).toBe(true)
      expect(store.hasBreakpoints).toBe(true)
      expect(store.hasAIAssistant).toBe(true)
      expect(store.hasDataPinning).toBe(true)
      expect(store.hasHumanCheckpoint).toBe(true)
      expect(store.showDebugUpgrade).toBe(false)
    })
  })

  // =========================================================================
  // Config Store: Load config
  // =========================================================================

  describe('config store', () => {
    it('should load config and populate all sections', async () => {
      getAllConfig.mockResolvedValueOnce({
        timing: {
          polling: { executionStatus: 500 },
          notifications: { successDuration: 2000 }
        },
        layout: {
          workflow: { horizontalSpacing: 400 }
        },
        llm: {
          providers: [
            { id: 'openai', name: 'OpenAI', models: [{ id: 'gpt-4', name: 'GPT-4' }] }
          ],
          defaults: { provider: 'openai', model: 'gpt-4' }
        },
        marketplace: {
          categories: ['automation', 'data', 'ai'],
          currencies: ['USD', 'EUR']
        },
        nodeDesign: {
          standard: { dimensions: { width: 280, height: 76 } },
          branch: { dimensions: { width: 76, height: 76 } }
        }
      })

      const store = useConfigStore()
      await store.loadConfig()

      // Verify real state hydration
      expect(store.isLoaded).toBe(true)
      expect(store.isLoading).toBe(false)

      // Verify config getters
      expect(store.getTiming('polling', 'executionStatus')).toBe(500)
      expect(store.getLayout('workflow', 'horizontalSpacing')).toBe(400)

      // LLM helpers
      const providers = store.getLLMProviders()
      expect(providers).toHaveLength(1)
      expect(providers[0].id).toBe('openai')
      expect(store.getLLMModels('openai')).toHaveLength(1)
      expect(store.getLLMDefaults()).toEqual({ provider: 'openai', model: 'gpt-4' })

      // Marketplace
      expect(store.getMarketplaceCategories()).toEqual(['automation', 'data', 'ai'])
      expect(store.getCurrencies()).toEqual(['USD', 'EUR'])

      // Node design
      const standardDims = store.getNodeDimensions('standard')
      expect(standardDims).toEqual({ width: 280, height: 76 })

      const branchDims = store.getNodeDimensions('branch')
      expect(branchDims).toEqual({ width: 76, height: 76 })

      // Unknown node type falls back to default
      const unknownDims = store.getNodeDimensions('nonexistent')
      expect(unknownDims).toEqual({ shape: 'rectangle', width: 240, height: 76 })
    })

    it('should not reload when already loaded', async () => {
      getAllConfig.mockResolvedValueOnce({ timing: {} })

      const store = useConfigStore()
      await store.loadConfig()
      await store.loadConfig() // should be no-op

      expect(getAllConfig).toHaveBeenCalledTimes(1)
    })

    it('should force refresh when requested', async () => {
      getAllConfig
        .mockResolvedValueOnce({ timing: { polling: { executionStatus: 1000 } } })
        .mockResolvedValueOnce({ timing: { polling: { executionStatus: 500 } } })

      const store = useConfigStore()
      await store.loadConfig()
      expect(store.getTiming('polling', 'executionStatus')).toBe(1000)

      await store.loadConfig(true) // forceRefresh
      expect(store.getTiming('polling', 'executionStatus')).toBe(500)
      expect(getAllConfig).toHaveBeenCalledTimes(2)
    })

    it('should handle config load error', async () => {
      getAllConfig.mockRejectedValueOnce(new Error('Config unavailable'))

      const store = useConfigStore()
      await store.loadConfig()

      expect(store.error).toBe('Config unavailable')
      expect(store.isLoaded).toBe(false)
      expect(store.isLoading).toBe(false)
    })

    it('should reset to defaults', async () => {
      getAllConfig.mockResolvedValueOnce({
        timing: { polling: { executionStatus: 500 } }
      })

      const store = useConfigStore()
      await store.loadConfig()
      expect(store.isLoaded).toBe(true)

      store.reset()

      expect(store.isLoaded).toBe(false)
      expect(store.error).toBeNull()
      // After reset, timing should have default values
      expect(store.getTiming('polling', 'executionStatus')).toBe(1000) // DEFAULTS value
    })
  })

  // =========================================================================
  // Feature Flag Helpers (standalone, 100% real)
  // =========================================================================

  describe('createCapabilityCheckers (100% real)', () => {
    it('should check capabilities from a ref', () => {
      const { ref } = require('vue')
      const capsRef = ref(['core.workflow_run', 'core.template_builder', 'local.metrics'])

      const { hasCapability, hasAnyCapability, hasAllCapabilities } = createCapabilityCheckers(capsRef)

      expect(hasCapability('core.workflow_run')).toBe(true)
      expect(hasCapability('nonexistent')).toBe(false)

      expect(hasAnyCapability('nonexistent', 'core.workflow_run')).toBe(true)
      expect(hasAnyCapability('a', 'b')).toBe(false)

      expect(hasAllCapabilities('core.workflow_run', 'local.metrics')).toBe(true)
      expect(hasAllCapabilities('core.workflow_run', 'nonexistent')).toBe(false)
    })
  })

  // =========================================================================
  // DEFAULT constants (verify fail-closed)
  // =========================================================================

  describe('default constants', () => {
    it('DEFAULT_CAPABILITIES should only include core features', () => {
      expect(DEFAULT_CAPABILITIES).toContain('core.workflow_run')
      expect(DEFAULT_CAPABILITIES).toContain('core.template_builder')
      expect(DEFAULT_CAPABILITIES).not.toContain('local.metrics')
      expect(DEFAULT_CAPABILITIES).not.toContain('execution.debug')
    })

    it('DEFAULT_FEATURES should be fail-closed', () => {
      expect(DEFAULT_FEATURES.marketplace).toBe(false)
      expect(DEFAULT_FEATURES.billing).toBe(false)
      expect(DEFAULT_FEATURES.observability).toBe(false)
    })

    it('DEFAULT_UI should hide most features', () => {
      expect(DEFAULT_UI.showMarketplace).toBe(false)
      expect(DEFAULT_UI.showObservability).toBe(false)
      expect(DEFAULT_UI.canUpgrade).toBe(true) // allow upgrade prompt
    })
  })
})
