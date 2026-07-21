/**
 * Templates API - Purchase Operations
 * Uses Gateway API instead of Firebase SDK
 */

import { get, post, put } from '@/api/client'

/**
 * Sync purchase to latest version
 */
export async function syncPurchase(purchaseId) {
  try {
    const result = await post(`/templates/purchases/${purchaseId}/sync`)

    return {
      ok: true,
      message: result.message || 'Synced successfully'
    }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

// ========== Fork Operations ==========

/**
 * Fork a template (create personal copy)
 * @param {string} templateId - Original template ID
 * @param {string|null} fromPurchaseId - If forking from a purchase, the purchase ID
 */
export async function forkTemplate(templateId, fromPurchaseId = null) {
  try {
    const result = await post(`/templates/${templateId}/fork`, {
      fromPurchaseId
    })

    return {
      ok: true,
      fork: result.fork || null,
      message: result.message || 'Forked successfully'
    }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

// ========== Fork Sync Operations ==========

/**
 * Get fork sync status (is the fork behind upstream?)
 */
export async function getForkSyncStatus(templateId, forkId) {
  try {
    const result = await get(`/templates/${templateId}/forks/${forkId}/sync-status`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Sync fork with upstream template
 */
export async function syncForkWithUpstream(templateId, forkId) {
  try {
    const result = await post(`/templates/${templateId}/forks/${forkId}/sync`)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

// ========== Merge Settings ==========

/**
 * Update merge protection settings
 */
export async function updateMergeSettings(templateId, settings) {
  try {
    const result = await put(`/templates/${templateId}/merge-settings`, settings)
    return { ok: true, merge_settings: result.merge_settings }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}
