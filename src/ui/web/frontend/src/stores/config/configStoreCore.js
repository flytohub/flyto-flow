import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { getAllConfig } from '@/api/platform'

const EMPTY_LLM_CONFIG = Object.freeze({
  providers: [],
  defaults: {
    provider: '',
    model: '',
    temperature: 0.7,
    maxTokens: 1000
  }
})

export const useConfigStore = defineStore('config', () => {
  const llm = ref({ ...EMPTY_LLM_CONFIG })
  const isLoaded = ref(false)
  const isLoading = ref(false)
  const error = ref(null)

  const llmProviders = computed(() => llm.value.providers || [])
  const defaultLLMProvider = computed(() => llm.value.defaults?.provider || '')
  const defaultLLMModel = computed(() => llm.value.defaults?.model || '')

  async function loadConfig(forceRefresh = false) {
    if (!forceRefresh && (isLoaded.value || isLoading.value)) return
    isLoading.value = true
    error.value = null
    try {
      const config = await getAllConfig({ forceRefresh })
      llm.value = config.llm || EMPTY_LLM_CONFIG
      isLoaded.value = true
    } catch (loadError) {
      error.value = loadError.message || 'Failed to load local configuration'
      llm.value = { ...EMPTY_LLM_CONFIG }
    } finally {
      isLoading.value = false
    }
  }

  function reset() {
    llm.value = { ...EMPTY_LLM_CONFIG }
    isLoaded.value = false
    isLoading.value = false
    error.value = null
  }

  return {
    llm,
    llmProviders,
    defaultLLMProvider,
    defaultLLMModel,
    isLoaded,
    isLoading,
    error,
    loadConfig,
    reset
  }
})
