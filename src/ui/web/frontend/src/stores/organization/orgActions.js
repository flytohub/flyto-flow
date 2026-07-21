/**
 * Organization Actions
 *
 * S-Grade: Organization CRUD operations.
 * Single responsibility: Fetch and update organization.
 */

import { organizationAPI } from '@/api/organization'
import i18n from '@/i18n'
import { telemetry } from '@/services/telemetry'
import { asObject } from '@/utils/dataBoundary'

/**
 * Create organization actions
 * @param {Object} state - State refs
 * @returns {Object} Organization action functions
 */
export function createOrgActions(state) {
  const { organization, isLoading, error } = state

  /**
   * Fetch current organization
   */
  async function fetchOrganization() {
    isLoading.value = true
    error.value = null

    try {
      const result = await organizationAPI.getCurrent()
      const normalized = asObject(result)
      if (normalized.ok) {
        const org = asObject(normalized.organization)
        organization.value = Object.keys(org).length > 0 ? org : null
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchOrganization')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update organization
   */
  async function updateOrganization(data) {
    if (!organization.value?.id) {
      return { ok: false, error: i18n.global.t('error.noOrganizationLoaded') }
    }

    isLoading.value = true
    error.value = null

    try {
      const result = await organizationAPI.update(organization.value.id, data)
      const normalized = asObject(result)
      if (normalized.ok) {
        telemetry.track('organization.update', {
          org_id: organization.value.id
        })
        organization.value = { ...organization.value, ...data }
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToUpdateOrganization')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  return {
    fetchOrganization,
    updateOrganization,
  }
}
