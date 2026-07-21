import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { packagesAPI } from '@/api/packages'

export const usePackageStore = defineStore('packages', () => {
  const packages = ref([])
  const loading = ref(false)
  const error = ref(null)
  const updatingIds = ref(new Set())
  const installingIds = ref(new Set())
  const removingIds = ref(new Set())

  const installedCount = computed(() => packages.value.filter(p => p.installed).length)
  const updatesAvailable = computed(() => packages.value.filter(p => p.updateAvailable).length)

  async function fetchStatus() {
    loading.value = true
    error.value = null
    try {
      const result = await packagesAPI.getStatus()
      packages.value = Array.isArray(result) ? result : []
    } catch (e) {
      error.value = e.userMessage || 'Failed to fetch package status'
    } finally {
      loading.value = false
    }
  }

  async function updatePackage(id) {
    updatingIds.value.add(id)
    try {
      const result = await packagesAPI.updatePackage(id)
      if (result.ok) {
        await fetchStatus()
      }
      return result
    } catch (e) {
      return { ok: false, message: e.userMessage || e.message || 'Update failed' }
    } finally {
      updatingIds.value.delete(id)
    }
  }

  async function installPackage(id) {
    installingIds.value.add(id)
    try {
      const result = await packagesAPI.installPackage(id)
      if (result.ok) {
        await fetchStatus()
      }
      return result
    } catch (e) {
      return { ok: false, message: e.userMessage || e.message || 'Install failed' }
    } finally {
      installingIds.value.delete(id)
    }
  }

  async function removePackage(id) {
    removingIds.value.add(id)
    try {
      const result = await packagesAPI.removePackage(id)
      if (result.ok) {
        await fetchStatus()
      }
      return result
    } catch (e) {
      return { ok: false, message: e.userMessage || e.message || 'Remove failed' }
    } finally {
      removingIds.value.delete(id)
    }
  }

  async function setAutoUpdate(id, enabled) {
    try {
      await packagesAPI.setAutoUpdate(id, enabled)
      const pkg = packages.value.find(p => p.id === id)
      if (pkg) pkg.autoUpdate = enabled
    } catch (e) {
      // revert on failure
      const pkg = packages.value.find(p => p.id === id)
      if (pkg) pkg.autoUpdate = !enabled
    }
  }

  async function updateAll() {
    const toUpdate = packages.value.filter(p => p.updateAvailable)
    const results = []
    for (const pkg of toUpdate) {
      results.push(await updatePackage(pkg.id))
    }
    return results
  }

  function isUpdating(id) {
    return updatingIds.value.has(id)
  }

  function isInstalling(id) {
    return installingIds.value.has(id)
  }

  function isRemoving(id) {
    return removingIds.value.has(id)
  }

  return {
    packages,
    loading,
    error,
    installedCount,
    updatesAvailable,
    fetchStatus,
    updatePackage,
    installPackage,
    removePackage,
    setAutoUpdate,
    updateAll,
    isUpdating,
    isInstalling,
    isRemoving,
  }
})
