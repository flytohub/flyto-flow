/**
 * AI Settings Store
 *
 * Manages BYOK (Bring Your Own Key) AI configuration state.
 * Config is stored server-side in ~/.flyto/ai_config.json (encrypted).
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { aiConfigAPI } from '@/api/aiConfig'
import { authAPI } from '@/api/auth'

export const useAISettingsStore = defineStore('aiSettings', () => {
  // ========== State ==========

  const provider = ref('openai')
  const apiKeyMasked = ref('')
  const model = ref('')
  const temperature = ref(0.7)
  const maxTokens = ref(4096)
  const baseUrl = ref('')
  const configured = ref(false)
  const loading = ref(false)
  const saving = ref(false)
  const testing = ref(false)
  const testResult = ref(null) // { ok, message, models? }
  const availableModels = ref([])
  const autoImport = ref(false)
  const autoExecute = ref(false)

  // ========== Getters ==========

  const isConfigured = computed(() => configured.value)

  const providerLabel = computed(() => {
    const labels = {
      openai: 'OpenAI',
      anthropic: 'Anthropic',
    }
    return labels[provider.value] || provider.value
  })

  const modelLabel = computed(() => {
    if (!model.value) return providerLabel.value
    // Shorten model names for display
    const m = model.value
    if (m.startsWith('gpt-4o')) return 'GPT-4o'
    if (m.startsWith('gpt-4')) return 'GPT-4'
    if (m.startsWith('gpt-3.5')) return 'GPT-3.5'
    if (m.includes('claude-opus')) return 'Claude Opus'
    if (m.includes('claude-sonnet')) return 'Claude Sonnet'
    if (m.includes('claude-haiku')) return 'Claude Haiku'
    return m
  })

  const needsApiKey = computed(() => {
    return true
  })

  const needsBaseUrl = computed(() => {
    return provider.value === 'openai-compatible'
  })

  const defaultModels = computed(() => {
    const defaults = {
      openai: ['gpt-4o', 'gpt-4o-mini'],
      anthropic: [
        'claude-sonnet-4-5-20250929',
        'claude-opus-4-6-20250116',
        'claude-sonnet-4-20250514',
        'claude-haiku-4-5-20251001',
      ],
      'openai-compatible': [],
    }
    return defaults[provider.value] || []
  })

  // ========== Actions ==========

  async function loadConfig() {
    // Skip for unauthenticated / expired-token callers; isLoggedIn() also
    // purges stale tokens so the next call finishes faster.
    if (!authAPI.isLoggedIn()) return
    loading.value = true
    try {
      const result = await aiConfigAPI.getConfig()
      if (result.ok && result.config) {
        provider.value = result.config.provider || 'openai'
        apiKeyMasked.value = result.config.apiKeyMasked || ''
        model.value = result.config.model || ''
        temperature.value = result.config.temperature ?? 0.7
        maxTokens.value = result.config.maxTokens ?? 4096
        baseUrl.value = result.config.baseUrl || ''
        autoImport.value = result.config.autoImport ?? false
        autoExecute.value = result.config.autoExecute ?? false
        configured.value = result.configured || false
      }
    } catch (err) {
      console.error('Failed to load AI config:', err)
    } finally {
      loading.value = false
    }
  }

  async function saveConfig({ apiKey } = {}) {
    saving.value = true
    try {
      const result = await aiConfigAPI.saveConfig({
        provider: provider.value,
        apiKey: apiKey || undefined,
        model: model.value,
        temperature: temperature.value,
        maxTokens: maxTokens.value,
        baseUrl: baseUrl.value,
        autoImport: autoImport.value,
        autoExecute: autoExecute.value
      })
      if (result.ok) {
        configured.value = true
        if (apiKey) {
          apiKeyMasked.value = '****' + apiKey.slice(-4)
        }
      }
      return result
    } catch (err) {
      return { ok: false, error: err.message }
    } finally {
      saving.value = false
    }
  }

  async function testConnection(apiKey) {
    testing.value = true
    testResult.value = null
    try {
      const result = await aiConfigAPI.testConnection({
        provider: provider.value,
        apiKey: apiKey || undefined,
        model: model.value || undefined,
        baseUrl: baseUrl.value || undefined
      })
      testResult.value = result
      if (result.ok && result.models) {
        availableModels.value = result.models
      }
      return result
    } catch (err) {
      testResult.value = { ok: false, error: err.message }
      return testResult.value
    } finally {
      testing.value = false
    }
  }

  function clearTestResult() {
    testResult.value = null
  }

  return {
    // State
    provider,
    apiKeyMasked,
    model,
    temperature,
    maxTokens,
    baseUrl,
    autoImport,
    autoExecute,
    configured,
    loading,
    saving,
    testing,
    testResult,
    availableModels,

    // Getters
    isConfigured,
    providerLabel,
    modelLabel,
    needsApiKey,
    needsBaseUrl,
    defaultModels,

    // Actions
    loadConfig,
    saveConfig,
    testConnection,
    clearTestResult
  }
})
