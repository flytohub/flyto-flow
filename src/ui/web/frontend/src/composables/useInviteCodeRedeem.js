import { ref } from 'vue'
import { templatesAPI } from '@/api/templates'

/**
 * Invite code redeem logic for Marketplace
 * @param {Object} options
 * @param {import('vue-router').Router} options.router - Vue Router instance
 * @param {Function} options.t - i18n translation function
 */
export function useInviteCodeRedeem({ router, t }) {
  const showRedeemInput = ref(false)
  const redeemCode = ref('')
  const isRedeeming = ref(false)
  const redeemError = ref('')
  const redeemSuccess = ref('')

  async function redeemInviteCode() {
    if (!redeemCode.value || isRedeeming.value) return

    isRedeeming.value = true
    redeemError.value = ''
    redeemSuccess.value = ''

    try {
      const result = await templatesAPI.redeemInviteKey(redeemCode.value.toUpperCase())

      if (result.ok) {
        redeemSuccess.value = t('marketplace.redeemSuccess', { name: result.template?.name || 'Template' })
        redeemCode.value = ''

        // Navigate to the template after a short delay
        setTimeout(() => {
          if (result.templateId) {
            router.push(`/templates/${result.templateId}`)
          }
        }, 1500)
      } else {
        redeemError.value = result.error || t('marketplace.redeemFailed')
      }
    } catch (err) {
      redeemError.value = err.message || t('marketplace.redeemFailed')
    } finally {
      isRedeeming.value = false
    }
  }

  return {
    showRedeemInput,
    redeemCode,
    isRedeeming,
    redeemError,
    redeemSuccess,
    redeemInviteCode,
  }
}
