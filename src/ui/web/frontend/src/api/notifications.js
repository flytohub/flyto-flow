/**
 * Notifications API - Gateway API Access
 * Single responsibility: Notification CRUD operations
 */

import { get, patch, post, del } from '@/api/client'
import { ENDPOINTS } from '@/api/config'
import { DEFAULTS } from '@/config/defaults'

/**
 * Get user notifications
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {number} params.page_size - Items per page
 * @param {boolean} params.unread_only - Only unread notifications
 * @returns {Promise<{ok: boolean, items: Array, total: number}>}
 */
export async function getNotifications(params = {}) {
  try {
    const { page = 1, page_size = DEFAULTS.PAGINATION.DEFAULT, unread_only = false } = params

    const result = await get(ENDPOINTS.NOTIFICATIONS.LIST, {
      params: {
        page,
        page_size,
        unread_only
      }
    })

    return {
      ok: true,
      items: result.items || [],
      total: result.total || 0
    }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message, items: [], total: 0 }
  }
}

/**
 * Get unread notification count
 * @returns {Promise<{ok: boolean, count: number}>}
 */
export async function getUnreadCount() {
  try {
    const result = await get(ENDPOINTS.NOTIFICATIONS.UNREAD_COUNT)
    return { ok: true, count: result.count || 0 }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message, count: 0 }
  }
}

/**
 * Mark notification as read
 * @param {string} notificationId - Notification ID
 * @returns {Promise<{ok: boolean}>}
 */
export async function markAsRead(notificationId) {
  try {
    await patch(ENDPOINTS.NOTIFICATIONS.MARK_READ(notificationId))
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Mark all notifications as read
 * @returns {Promise<{ok: boolean, count: number}>}
 */
export async function markAllAsRead() {
  try {
    const result = await post(ENDPOINTS.NOTIFICATIONS.MARK_ALL_READ)
    return { ok: true, count: result.count || 0 }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message, count: 0 }
  }
}

/**
 * Delete a notification
 * @param {string} notificationId - Notification ID
 * @returns {Promise<{ok: boolean}>}
 */
export async function deleteNotification(notificationId) {
  try {
    await del(ENDPOINTS.NOTIFICATIONS.GET(notificationId))
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

export default {
  getNotifications,
  getUnreadCount,
  markAsRead,
  markAllAsRead,
  deleteNotification
}
