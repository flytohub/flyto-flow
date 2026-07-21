/**
 * Capabilities Store Core
 *
 * S-Grade: System capabilities management using dual-axis model.
 * Uses extracted helpers for page access and capability checks.
 *
 * SECURITY NOTE:
 * - isPro and isAdmin are SERVER-COMPUTED values
 * - Do NOT compute these client-side to prevent bypass
 * - Backend computes: is_pro = (license_type != FREE) OR is_admin
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { capabilitiesAPI } from '@/api/capabilities'
import { isAlwaysAllowed, checkPageAccess } from './pageAccessHelpers'
import {
  createCapabilityCheckers,
  DEFAULT_CAPABILITIES,
  DEFAULT_FEATURES,
  DEFAULT_UI
} from './featureFlagHelpers'
import { asArray, asBoolean, asInteger, asObject, asString } from '@/utils/dataBoundary'

export const useCapabilitiesStore = defineStore('capabilities', () => {
  // ========== State ==========
  const deploymentMode = ref('local_offline')
  const licenseType = ref('free')
  const billingMode = ref('preview')
  const isLicensed = ref(false)
  const _isPro = ref(false)      // Server-computed: isPaid OR isAdmin
  const _isAdmin = ref(false)    // Server-provided admin status
  const capabilities = ref([])
  const features = ref({})
  const pages = ref({})
  const ui = ref({})
  const isLoaded = ref(false)
  const isLoading = ref(false)
  const error = ref(null)

  // Trial state (server-computed)
  const trialState = ref(null)         // 'not_started' | 'active' | 'expired' | 'paid'
  const trialExpiresAt = ref(null)     // ISO string
  const trialDaysRemaining = ref(null) // number

  // ========== Deployment Mode Getters ==========
  const isCloud = computed(() => deploymentMode.value === 'saas_cloud')
  const isLocalOnline = computed(() => deploymentMode.value === 'local_online')
  const isLocalOffline = computed(() => deploymentMode.value === 'local_offline')
  const isEnterprise = computed(() => deploymentMode.value === 'enterprise_intranet')
  const isOffline = computed(() => deploymentMode.value === 'local_offline')

  // ========== License Type Getters ==========
  const isFree = computed(() => licenseType.value === 'free')
  const isSubscription = computed(() => licenseType.value === 'subscription')
  const isOfflineLicense = computed(() => licenseType.value === 'offline_license')
  const isEnterpriseLicense = computed(() => licenseType.value === 'enterprise')
  const isPaid = computed(() => licenseType.value !== 'free')
  const isBillingPreview = computed(() => billingMode.value === 'preview')
  // S-Grade: isPro comes directly from server (server computes: isPaid OR isAdmin)
  // This is the single source of truth for all Pro feature checks
  // SECURITY: Do NOT compute this client-side - use the server value
  const isPro = computed(() => _isPro.value)
  const isAdmin = computed(() => _isAdmin.value)

  // ========== Feature Flags ==========
  const hasMarketplace = computed(() => features.value.marketplace ?? false)
  const hasBilling = computed(() => features.value.billing ?? false)
  const hasRbac = computed(() => features.value.rbac ?? false)
  const hasAudit = computed(() => features.value.audit ?? false)
  const hasSso = computed(() => features.value.sso ?? false)
  const hasRunners = computed(() => features.value.runners ?? false)
  const hasVault = computed(() => features.value.vault ?? false)
  const hasApprovals = computed(() => features.value.approvals ?? false)
  const hasSelfSignup = computed(() => features.value.selfSignup ?? true)
  const hasOrganization = computed(() => features.value.organization ?? false)
  const hasObservability = computed(() => features.value.observability ?? false)
  const hasVersioning = computed(() => features.value.versioning ?? false)
  const hasSubscriptions = computed(() => features.value.subscriptions ?? false)

  // Capability-based features
  const hasMetrics = computed(() => capabilities.value.includes('local.metrics'))
  const hasTracing = computed(() => capabilities.value.includes('local.tracing'))
  const hasAlerts = computed(() => capabilities.value.includes('local.alerts'))
  const hasAuditChain = computed(() => capabilities.value.includes('local.audit_chain'))
  const hasExecutionReplay = computed(() => capabilities.value.includes('execution.replay'))
  const hasExecutionRerun = computed(() => capabilities.value.includes('execution.rerun'))
  const hasExecutionDebug = computed(() => capabilities.value.includes('execution.debug'))
  const hasExecutionRecordFull = computed(() => capabilities.value.includes('core.execution_record_full'))
  const hasRecording = computed(() => capabilities.value.includes('desktop.workflow_recording'))

  // All features always available (no Pro gate)
  const hasEvidence = computed(() => capabilities.value.includes('execution.evidence') || _isPro.value)
  const hasLineage = computed(() => capabilities.value.includes('execution.lineage') || _isPro.value)
  const hasReplay = computed(() => true)
  const hasTests = computed(() => true)
  const hasVersions = computed(() => true)
  const hasBreakpoints = computed(() => true)
  const hasAIAssistant = computed(() => true)
  const hasDataPinning = computed(() => true)
  const hasHumanCheckpoint = computed(() => true)
  const showDebugUpgrade = computed(() => false)

  // ========== UI Visibility ==========
  const showMarketplace = computed(() => ui.value.showMarketplace ?? false)
  const showBilling = computed(() => ui.value.showBilling ?? false)
  const showOrgSettings = computed(() => ui.value.showOrgSettings ?? false)
  const showAuditLog = computed(() => ui.value.showAudit ?? false)
  const showRbacSettings = computed(() => ui.value.showRbacSettings ?? false)
  const showObservability = computed(() => ui.value.showObservability ?? false)
  const showVersioning = computed(() => ui.value.showVersioning ?? false)
  const showSsoSettings = computed(() => ui.value.showSsoSettings ?? false)
  const showSubscriptions = computed(() => ui.value.showSubscriptions ?? false)
  const allowSelfSignup = computed(() => ui.value.allowSelfSignup ?? true)
  const authMethod = computed(() => ui.value.authMethod ?? 'firebase')
  const canUpgrade = computed(() => ui.value.canUpgrade ?? isFree.value)
  const upgradeUrl = computed(() => ui.value.upgradeUrl ?? '/pricing')
  const upgradeFeatures = computed(() => ui.value.upgradeFeatures ?? [])

  // Trial computed
  const isTrialActive = computed(() => trialState.value === 'active')
  const isTrialExpired = computed(() => trialState.value === 'expired')

  // ========== Actions ==========
  const { hasCapability, hasAnyCapability, hasAllCapabilities } = createCapabilityCheckers(capabilities)

  async function load() {
    if (isLoaded.value || isLoading.value) return

    isLoading.value = true
    error.value = null

    try {
      // Single API call - backend computes everything
      const data = asObject(await capabilitiesAPI.getCapabilities())
      // Note: client.js converts snake_case to camelCase automatically
      deploymentMode.value = asString(data.deploymentMode, 'local_offline')
      licenseType.value = asString(data.licenseType, 'free')
      billingMode.value = asString(data.billingMode, 'preview')
      isLicensed.value = asBoolean(data.isLicensed, false)
      // Server-computed Pro and Admin status (authoritative)
      _isPro.value = asBoolean(data.isPro, false)
      _isAdmin.value = asBoolean(data.isAdmin, false)
      capabilities.value = asArray(data.capabilities)
      features.value = asObject(data.features)
      pages.value = asObject(data.pages)
      ui.value = asObject(data.ui)
      // Trial fields
      trialState.value = data.trialState || null
      trialExpiresAt.value = data.trialExpiresAt || null
      trialDaysRemaining.value = data.trialDaysRemaining == null ? null : asInteger(data.trialDaysRemaining, 0)
      isLoaded.value = true
    } catch (err) {
      error.value = err.message || 'Failed to load capabilities'
      // Set defaults on error - fail CLOSED for security (no Pro access)
      deploymentMode.value = 'local_offline'
      licenseType.value = 'free'
      billingMode.value = 'preview'
      isLicensed.value = false
      _isPro.value = false  // Fail closed - no Pro on error
      _isAdmin.value = false
      capabilities.value = DEFAULT_CAPABILITIES
      features.value = DEFAULT_FEATURES
      pages.value = {}
      ui.value = DEFAULT_UI
      trialState.value = null
      trialExpiresAt.value = null
      trialDaysRemaining.value = null
      isLoaded.value = true
    } finally {
      isLoading.value = false
    }
  }

  async function reload() {
    isLoaded.value = false
    return load()
  }

  function canAccessPage(path) {
    // Backend config is authoritative — check it first
    const result = checkPageAccess(path, pages.value)
    if (result !== null) return result
    // Fallback to always-allowed list only if backend has no config for this path
    if (isAlwaysAllowed(path)) return true
    return false
  }

  function getExplicitPageAccess(path) {
    return checkPageAccess(path, pages.value)
  }

  async function waitForLoad(timeoutMs = 5000) {
    if (isLoaded.value) return true
    if (!isLoading.value) load()

    return new Promise((resolve) => {
      const startTime = Date.now()
      const checkInterval = setInterval(() => {
        if (isLoaded.value) {
          clearInterval(checkInterval)
          resolve(true)
        } else if (Date.now() - startTime > timeoutMs) {
          clearInterval(checkInterval)
          resolve(false)
        }
      }, 100)
    })
  }

  function reset() {
    deploymentMode.value = 'cloud'
    licenseType.value = 'free'
    billingMode.value = 'preview'
    isLicensed.value = false
    _isPro.value = false
    _isAdmin.value = false
    capabilities.value = []
    features.value = {}
    pages.value = {}
    ui.value = {}
    trialState.value = null
    trialExpiresAt.value = null
    trialDaysRemaining.value = null
    isLoaded.value = false
    isLoading.value = false
    error.value = null
  }

  return {
    // State
    deploymentMode, licenseType, billingMode, isLicensed, capabilities, features, pages, ui,
    isLoaded, isLoading, error,
    // Deployment mode
    isCloud, isLocalOnline, isLocalOffline, isEnterprise, isOffline,
    // License type (isPro and isAdmin are server-computed, authoritative)
    isFree, isSubscription, isOfflineLicense, isEnterpriseLicense, isPaid, isBillingPreview, isPro, isAdmin,
    // Feature flags
    hasMarketplace, hasBilling, hasRbac, hasAudit, hasSso, hasRunners,
    hasVault, hasApprovals, hasSelfSignup, hasOrganization, hasObservability,
    hasVersioning, hasSubscriptions, hasMetrics, hasTracing, hasAlerts, hasAuditChain,
    hasExecutionReplay, hasExecutionRerun, hasExecutionDebug, hasExecutionRecordFull, hasRecording,
    // All features always available (no Pro gate)
    hasEvidence, hasLineage, hasReplay, hasTests, hasVersions, hasBreakpoints,
    hasAIAssistant, hasDataPinning, hasHumanCheckpoint, showDebugUpgrade,
    // UI visibility
    showMarketplace, showBilling, showOrgSettings, showAuditLog, showRbacSettings,
    showObservability, showVersioning, showSsoSettings, showSubscriptions, allowSelfSignup, authMethod,
    canUpgrade, upgradeUrl, upgradeFeatures,
    // Trial
    trialState, trialExpiresAt, trialDaysRemaining,
    isTrialActive, isTrialExpired,
    // Actions
    load, reload, hasCapability, hasAnyCapability, hasAllCapabilities,
    canAccessPage, getExplicitPageAccess, waitForLoad, reset
  }
})
