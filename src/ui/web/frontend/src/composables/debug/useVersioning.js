/**
 * useVersioning Composable
 * Manages module version selection and locking
 */

import { ref, computed } from 'vue'
import { versioningAPI } from '@/api/versioning'

export function useVersioning(options = {}) {
  const { onError, onSuccess } = options

  // State
  const versions = ref([])
  const selectedVersion = ref(null)
  const workflowLocks = ref({})
  const moduleMetadata = ref(null)
  const availableUpdates = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  // Computed
  const latestVersion = computed(() => versions.value[0] || null)

  const versionCount = computed(() => versions.value.length)

  const lockedModules = computed(() => Object.keys(workflowLocks.value))

  const lockCount = computed(() => lockedModules.value.length)

  const hasUpdates = computed(() => availableUpdates.value.length > 0)

  const hasVersions = computed(() => versions.value.length > 0)

  // Actions
  async function loadVersions(moduleId) {
    isLoading.value = true
    error.value = null

    try {
      const data = await versioningAPI.listVersions(moduleId)
      versions.value = data.versions || []
      return { ok: true, data: versions.value }
    } catch (err) {
      error.value = err.message || err.userMessage || 'Failed to load versions'
      onError?.(err)
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function getLatestVersion(moduleId) {
    try {
      const data = await versioningAPI.getLatestVersion(moduleId)
      return { ok: true, version: data.version, metadata: data.metadata }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  async function resolveVersion(moduleId, constraint) {
    try {
      const data = await versioningAPI.resolveVersion(moduleId, constraint)
      return { ok: true, version: data.version, metadata: data.metadata }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  async function loadModuleMetadata(moduleId, version) {
    isLoading.value = true
    try {
      const data = await versioningAPI.getModuleMetadata(moduleId, version)
      moduleMetadata.value = data
      return { ok: true, data }
    } catch (err) {
      error.value = err.message || err.userMessage || 'Failed to load metadata'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function loadWorkflowLocks(workflowId) {
    try {
      const data = await versioningAPI.getWorkflowLocks(workflowId)
      workflowLocks.value = data.locks || {}
      return { ok: true, data: workflowLocks.value }
    } catch (err) {
      error.value = err.message || err.userMessage || 'Failed to load locks'
      return { ok: false, error: error.value }
    }
  }

  async function setVersionLock(workflowId, moduleId, version) {
    isLoading.value = true
    try {
      const data = await versioningAPI.setWorkflowLock(workflowId, moduleId, version)
      workflowLocks.value[moduleId] = version
      onSuccess?.('version_locked')
      return { ok: true, data }
    } catch (err) {
      error.value = err.message || err.userMessage || 'Failed to set lock'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function removeVersionLock(workflowId, moduleId) {
    isLoading.value = true
    try {
      await versioningAPI.removeWorkflowLock(workflowId, moduleId)
      delete workflowLocks.value[moduleId]
      workflowLocks.value = { ...workflowLocks.value }
      onSuccess?.('version_unlocked')
      return { ok: true }
    } catch (err) {
      error.value = err.message || err.userMessage || 'Failed to remove lock'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function getChangelog(moduleId, version) {
    try {
      const data = await versioningAPI.getChangelog(moduleId, version)
      return { ok: true, data }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  async function checkUpdates(workflowId) {
    try {
      const data = await versioningAPI.checkUpdates(workflowId)
      availableUpdates.value = data.updates || []
      return { ok: true, data: availableUpdates.value }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  function selectVersion(version) {
    selectedVersion.value = version
  }

  function isLocked(moduleId) {
    return moduleId in workflowLocks.value
  }

  function getLockedVersion(moduleId) {
    return workflowLocks.value[moduleId] || null
  }

  function clearVersions() {
    versions.value = []
    selectedVersion.value = null
    moduleMetadata.value = null
    error.value = null
  }

  function reset() {
    clearVersions()
    workflowLocks.value = {}
    availableUpdates.value = []
  }

  return {
    // State
    versions,
    selectedVersion,
    workflowLocks,
    moduleMetadata,
    availableUpdates,
    isLoading,
    error,

    // Computed
    latestVersion,
    versionCount,
    lockedModules,
    lockCount,
    hasUpdates,
    hasVersions,

    // Actions
    loadVersions,
    getLatestVersion,
    resolveVersion,
    loadModuleMetadata,
    loadWorkflowLocks,
    setVersionLock,
    removeVersionLock,
    getChangelog,
    checkUpdates,
    selectVersion,
    isLocked,
    getLockedVersion,
    clearVersions,
    reset
  }
}

export default useVersioning
