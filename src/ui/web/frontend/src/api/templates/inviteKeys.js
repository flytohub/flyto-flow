/**
 * Templates API - Invite Key Operations
 * Uses Gateway API instead of Firebase SDK
 */

import { get, post, del } from '@/api/client'
import i18n from '@/i18n'

/**
 * Create invite key for template
 * @param {string} templateId - Template ID
 * @param {Object} options - Key options
 * @param {number} options.maxUses - Maximum uses (1-1000)
 * @param {number|null} options.expiresInDays - Days until expiration (null = no expiration)
 * @param {string} options.note - Optional note
 */
export async function createInviteKey(templateId, options = {}) {
  try {
    const { maxUses = 1, expiresInDays = null, note = null } = options

    const result = await post(`/templates/${templateId}/invite-keys`, {
      maxUses,
      expiresInDays,
      note
    })

    if (!result.ok) {
      return { ok: false, error: result.error || i18n.global.t('error.failedToCreateInviteKey') }
    }

    return {
      ok: true,
      key: result.key
    }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * List invite keys for template
 */
export async function listInviteKeys(templateId) {
  try {
    const result = await get(`/templates/${templateId}/invite-keys`)

    return {
      ok: true,
      keys: result.keys || []
    }
  } catch (err) {
    return { ok: false, error: err.message, keys: [] }
  }
}

/**
 * Redeem invite key to get access to a private template
 * @param {string} key - The invite key code
 */
export async function redeemInviteKey(key) {
  try {
    const result = await post('/templates/invite-keys/redeem', { key })

    if (!result.ok) {
      return { ok: false, error: result.error || i18n.global.t('error.invalidOrExpiredKey') }
    }

    return {
      ok: true,
      template: result.template,
      templateId: result.templateId
    }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Revoke invite key
 * @param {string} templateId - Template ID
 * @param {string} keyId - Key ID to revoke
 */
export async function revokeInviteKey(templateId, keyId) {
  try {
    const result = await del(`/templates/${templateId}/invite-keys/${keyId}`)
    return { ok: result.ok !== false }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}
