/**
 * Plugin Install Actions
 *
 * S-Grade: Install/uninstall actions.
 * Single responsibility: Plugin installation operations.
 */

import { pluginAPI } from '@/api/plugins'
import i18n from '@/i18n'
import { telemetry } from '@/services/telemetry'

/**
 * Create install actions
 * @param {Object} state - State refs
 * @returns {Object} Install action functions
 */
export function createInstallActions(state) {
  const { installedPlugins, isLoading, isInstalling, error } = state

  /**
   * Fetch installed plugins
   */
  async function fetchInstalled(params = {}) {
    isLoading.value = true
    error.value = null

    try {
      const result = await pluginAPI.listInstalled(params)
      if (result.ok) {
        installedPlugins.value = result.data?.plugins || result.data || []
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchInstalledPlugins')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Install a model
   */
  async function installModel(modelId) {
    isInstalling.value = true
    error.value = null

    try {
      const result = await pluginAPI.installModel(modelId)
      if (result.ok) {
        telemetry.track('plugin.install', {
          model_id: modelId
        })
        // Refresh installed list
        await fetchInstalled()
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToInstallModel')
      return { ok: false, error: error.value }
    } finally {
      isInstalling.value = false
    }
  }

  /**
   * Uninstall a model
   */
  async function uninstallModel(modelId) {
    isInstalling.value = true
    error.value = null

    try {
      const result = await pluginAPI.uninstallModel(modelId)
      if (result.ok) {
        telemetry.track('plugin.uninstall', {
          model_id: modelId
        })
        // Remove from local list
        installedPlugins.value = installedPlugins.value.filter(
          p => p.id !== modelId && p.modelId !== modelId
        )
      } else {
        error.value = result.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToUninstallModel')
      return { ok: false, error: error.value }
    } finally {
      isInstalling.value = false
    }
  }

  return {
    fetchInstalled,
    installModel,
    uninstallModel,
  }
}
