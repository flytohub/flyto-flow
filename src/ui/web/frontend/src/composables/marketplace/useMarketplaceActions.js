/**
 * Marketplace Actions Composable
 *
 * S-Grade: Template installation and purchase actions.
 * Single responsibility: marketplace operations.
 */
import { ref, computed } from 'vue'
import { templatesAPI } from '@/api/templates'
import { createCheckoutSession } from '@/api/payment'
import { safeRedirect } from '@/utils/safeRedirect'
import { trackMarketplace } from '@/utils/telemetryTracker'

/**
 * Create marketplace actions
 * @param {Object} options
 * @param {Function} options.onSuccess - Success callback
 * @param {Function} options.onError - Error callback
 * @returns {Object} Action methods and state
 */
export function useMarketplaceActions({ onSuccess, onError } = {}) {
  // State
  const installingId = ref(null)

  // Remove confirmation dialog state
  const showRemoveDialog = ref(false)
  const removeTarget = ref(null)

  /** Returns an i18n key for the warning text (resolved by the view via t()). */
  const removeWarningKey = computed(() => {
    const tmpl = removeTarget.value
    if (!tmpl) return ''
    const ctx = tmpl.purchase_context || {}
    if (ctx.source_deleted || ctx.source_unpublished) {
      return 'marketplace.removeWarningDelisted'
    }
    const source = ctx.source
    if (source === 'installed' || source === 'invite_key') {
      return 'marketplace.removeWarningMayDelist'
    }
    return ''
  })

  /**
   * Install a template
   */
  async function installTemplate(template) {
    if (installingId.value) return

    installingId.value = template.id
    try {
      const result = await templatesAPI.addToLibrary(template.id, 'installed')
      if (!result.ok) {
        throw new Error(result.error || 'Install failed')
      }
      template.isInstalled = true

      trackMarketplace.install(
        template.id,
        template.name,
        template.pricing,
        template.categorySlug
      )

      onSuccess?.('installed')
      return true
    } catch (err) {
      onError?.(err)
      return false
    } finally {
      installingId.value = null
    }
  }

  /**
   * Request removal — shows confirmation dialog if template needs a warning,
   * otherwise removes immediately.
   */
  function removeTemplate(template) {
    if (installingId.value) return

    const ctx = template.purchase_context || {}
    const source = ctx.source
    const needsWarning =
      ctx.source_deleted ||
      ctx.source_unpublished ||
      source === 'installed' ||
      source === 'invite_key'

    if (needsWarning) {
      removeTarget.value = template
      showRemoveDialog.value = true
    } else {
      confirmRemoveTemplate(template)
    }
  }

  /**
   * Confirm and execute the removal
   */
  async function confirmRemoveTemplate(template) {
    const target = template || removeTarget.value
    if (!target) return

    showRemoveDialog.value = false
    installingId.value = target.id

    try {
      const result = await templatesAPI.removeFromLibrary(target.id)
      if (!result.ok) {
        throw new Error(result.error || 'Remove failed')
      }
      target.isInstalled = false

      trackMarketplace.uninstall(target.id)

      onSuccess?.('removed')
      return true
    } catch (err) {
      onError?.(err)
      return false
    } finally {
      installingId.value = null
      removeTarget.value = null
    }
  }

  function cancelRemoveTemplate() {
    showRemoveDialog.value = false
    removeTarget.value = null
  }

  /**
   * Initiate template purchase
   */
  async function purchaseTemplate(template, successUrl, cancelUrl) {
    try {
      trackMarketplace.purchaseStart(
        template.id,
        template.price,
        template.currency || 'usd'
      )

      const response = await createCheckoutSession(template.id, successUrl, cancelUrl)

      // Backend returns session_url -> camelCased to sessionUrl by the response interceptor
      if (response.ok && response.sessionUrl) {
        safeRedirect(response.sessionUrl)
        return true
      } else {
        throw new Error(response.error || 'Purchase failed')
      }
    } catch (err) {
      onError?.(err)
      return false
    }
  }

  return {
    // State
    installingId,

    // Remove dialog state
    showRemoveDialog,
    removeTarget,
    removeWarningKey,

    // Methods
    installTemplate,
    removeTemplate,
    confirmRemoveTemplate,
    cancelRemoveTemplate,
    purchaseTemplate
  }
}

export default useMarketplaceActions
