/**
 * Templates API - User Library Operations
 * Uses Gateway API instead of Firebase SDK
 */

import { get, post, del, patch } from '@/api/client'
import { normalizeTemplate } from './helpers'
import i18n from '@/i18n'

/**
 * Get user's library (saved/purchased/installed templates)
 * Now returns templates from snapshots with purchase context
 * @param {Object} params
 * @param {boolean} params.excludeOwn - Exclude user's own created templates
 * @param {string} params.sortBy - Sort: created|updated|name
 */
export async function getLibrary(params = {}) {
  try {
    const queryParams = {}
    if (params.excludeOwn) queryParams.exclude_own = true
    if (params.sortBy) queryParams.sort_by = params.sortBy

    const result = await get('/templates/library', { params: queryParams })

    if (!result.ok) {
      return { ok: false, error: result.error, items: [] }
    }

    const items = (result.templates || []).map(t => {
      const item = normalizeTemplate(t, t.id)
      item.templateId = t.templateId || t.id

      // Add purchase context fields (from snapshot-based storage)
      if (t.purchaseContext) {
        item.purchaseContext = t.purchaseContext
        item.hasUpdate = t.purchaseContext.hasUpdate || false
        item.sourceDeleted = t.purchaseContext.sourceDeleted || false
        item.sourceUnpublished = t.purchaseContext.sourceUnpublished || false
        item.purchaseId = t.purchaseContext.purchaseId
        item.purchasedVersion = t.purchaseContext.purchasedVersion
        item.currentVersion = t.purchaseContext.currentVersion
      }

      // Add fork context fields
      if (t.forkContext) {
        item.forkContext = t.forkContext
        item.isFork = true
        item.forkId = t.forkContext.forkId
        item.sourceTemplateId = t.forkContext.sourceTemplateId
      }

      return item
    })

    return { ok: true, items }
  } catch (err) {
    return { ok: false, error: err.message, items: [] }
  }
}

/**
 * Add template to library
 */
export async function addToLibrary(templateId, source = 'saved') {
  try {
    const result = await post(`/templates/library/${templateId}`, null, {
      params: { source }
    })

    // Check if backend indicated failure
    if (result.ok === false) {
      return { ok: false, error: result.error || 'Add to library failed' }
    }

    return { ok: true, message: result.message || i18n.global.t('message.addedToLibrary') }
  } catch (err) {
    console.error('[addToLibrary] error:', err)
    return { ok: false, error: err.message }
  }
}

/**
 * Remove template from library
 */
export async function removeFromLibrary(templateId) {
  try {
    await del(`/templates/library/${templateId}`)
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Batch remove templates from library (parallel on backend)
 */
export async function batchRemoveFromLibrary(templateIds) {
  try {
    const result = await post('/templates/library/batch-remove', { template_ids: templateIds })
    return { ok: true, deleted: result.deleted, failed: result.failed }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Update library item settings
 * @param {string} libraryId - Library item ID
 * @param {Object} settings - Settings to update
 * @param {string} settings.autoUpdate - Auto-update policy (off|patch|minor|all)
 * @returns {Promise<Object>} Update result
 */
export async function updateLibrarySettings(libraryId, settings) {
  try {
    const result = await patch(`/templates/library/${libraryId}/settings`, settings)

    return { ok: result.ok, message: result.message, error: result.error }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}
