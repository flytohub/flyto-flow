import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { capabilitiesAPI } from '@/api/capabilities'
import { asArray, asObject } from '@/utils/dataBoundary'

const CE_ROUTES = [
  '/',
  '/my-templates',
  '/templates',
  '/executions',
  '/mcp',
  '/variables',
  '/observability'
]

export const useCapabilitiesStore = defineStore('capabilities', () => {
  const capabilities = ref([])
  const isLoaded = ref(false)
  const isLoading = ref(false)
  const error = ref(null)

  const hasCapability = capability => capabilities.value.includes(capability)
  const hasAnyCapability = (...items) => items.some(hasCapability)
  const hasAllCapabilities = (...items) => items.every(hasCapability)

  const hasEvidence = computed(() => hasCapability('execution.evidence'))
  const hasLineage = computed(() => hasCapability('execution.lineage'))
  const hasReplay = computed(() => true)
  const hasTests = computed(() => true)
  const hasVersions = computed(() => true)
  const hasBreakpoints = computed(() => true)
  const hasDataPinning = computed(() => true)
  const hasHumanCheckpoint = computed(() => true)
  const hasRecording = computed(() => hasCapability('desktop.workflow_recording'))

  async function load() {
    if (isLoaded.value || isLoading.value) return
    isLoading.value = true
    error.value = null
    try {
      const data = asObject(await capabilitiesAPI.getCapabilities())
      capabilities.value = asArray(data.capabilities)
    } catch (loadError) {
      error.value = loadError.message || 'Failed to load local capabilities'
      capabilities.value = []
    } finally {
      isLoaded.value = true
      isLoading.value = false
    }
  }

  async function reload() {
    isLoaded.value = false
    return load()
  }

  function canAccessPage(path) {
    return CE_ROUTES.some(route => path === route || path.startsWith(`${route}/`))
  }

  async function waitForLoad() {
    await load()
    return isLoaded.value
  }

  function reset() {
    capabilities.value = []
    isLoaded.value = false
    isLoading.value = false
    error.value = null
  }

  return {
    capabilities,
    isLoaded,
    isLoading,
    error,
    hasEvidence,
    hasLineage,
    hasReplay,
    hasTests,
    hasVersions,
    hasBreakpoints,
    hasDataPinning,
    hasHumanCheckpoint,
    hasRecording,
    hasCapability,
    hasAnyCapability,
    hasAllCapabilities,
    canAccessPage,
    load,
    reload,
    waitForLoad,
    reset
  }
})
