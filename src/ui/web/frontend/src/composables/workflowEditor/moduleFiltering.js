/**
 * Module Filtering — Compatibility filtering for module selection
 *
 * Manages the state and API calls for filtering modules based on
 * connection compatibility (type safety).
 */

import { ref } from 'vue'
import { getConnectableModules as getConnectableModulesAPI, getConnectableForReplacement } from '@/api/modules'

/**
 * Creates a module filtering subsystem with reactive state.
 *
 * @returns {Object} Filtering state and methods
 */
export function createModuleFiltering() {
  const isLoadingCompatible = ref(false)
  const compatibleModuleIds = ref(new Set())

  function filterModules(modules) {
    if (isLoadingCompatible.value || compatibleModuleIds.value.size === 0) {
      return modules
    }
    return modules.filter(m => {
      const moduleId = m.moduleId || m.module || m.module_id
      // Template modules use canConnectTo: ["*"] / canReceiveFrom: ["*"],
      // so they are always compatible — bypass the connectable filter
      if (moduleId?.startsWith('template.invoke:')) return true
      return compatibleModuleIds.value.has(moduleId)
    })
  }

  async function fetchCompatibleModules(sourceModuleId) {
    if (!sourceModuleId) {
      compatibleModuleIds.value = new Set()
      return compatibleModuleIds.value
    }

    isLoadingCompatible.value = true
    try {
      const response = await getConnectableModulesAPI(sourceModuleId, { direction: 'next' })
      const moduleIds = (response.modules || []).map(m => m.moduleId || m.module_id)
      compatibleModuleIds.value = new Set(moduleIds)
    } catch (err) {
      compatibleModuleIds.value = new Set()
    } finally {
      isLoadingCompatible.value = false
    }
    return compatibleModuleIds.value
  }

  async function fetchReplacementCompatibleModules(upstreamModuleId, downstreamModuleId) {
    isLoadingCompatible.value = true
    try {
      const response = await getConnectableForReplacement({
        upstreamModule: upstreamModuleId,
        downstreamModule: downstreamModuleId,
        limit: 200
      })
      const moduleIds = (response.modules || []).map(m => m.moduleId || m.module_id)
      compatibleModuleIds.value = new Set(moduleIds)
    } catch (err) {
      compatibleModuleIds.value = new Set()
    } finally {
      isLoadingCompatible.value = false
    }
    return compatibleModuleIds.value
  }

  function clearCompatibleModules() {
    compatibleModuleIds.value = new Set()
  }

  return {
    isLoadingCompatible,
    filterModules,
    fetchCompatibleModules,
    fetchReplacementCompatibleModules,
    clearCompatibleModules
  }
}
