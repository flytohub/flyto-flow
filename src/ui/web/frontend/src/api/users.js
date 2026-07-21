/**
 * Users API - Gateway API Access
 * Handles user profiles, follow system, and notifications
 */

import { get, post, del } from '@/api/client'
import i18n from '@/i18n'
import { ENDPOINTS } from '@/api/config'
import { DEFAULTS } from '@/config/defaults'
import { authAPI } from '@/api/auth'
import { getCurrentUserId } from '@/utils/auth'
import {
  asBoolean,
  asNonNegativeInteger,
  asObject,
  asString,
  normalizeCreatorProfile,
  normalizeCreatorTemplatesResponse,
  normalizePeopleListResponse
} from '@/utils/dataBoundary'

// =============================================================================
// Utility Functions (DRY - extract repeated transformations)
// =============================================================================

/**
 * Normalize user profile from API response
 * @param {Object} data - Raw API response data (already camelCase from client.js interceptor)
 * @param {Object} extras - Additional fields to merge
 * @returns {Object} Normalized user profile
 */
function normalizeUser(data, extras = {}) {
  const raw = asObject(data)
  // client.js auto-converts snake_case to camelCase, so only read camelCase
  return normalizeCreatorProfile({
    ...raw,
    id: raw.id,
    uid: raw.id,
    email: raw.email || null,
    displayName: asString(raw.displayName, ''),
    avatarUrl: raw.avatarUrl || null,
    bio: raw.bio || null,
    website: raw.website || null,
    isCreator: asBoolean(raw.isCreator, false),
    createdAt: raw.createdAt || null,
    followersCount: asNonNegativeInteger(raw.followersCount, 0),
    followingCount: asNonNegativeInteger(raw.followingCount, 0),
    isFollowing: asBoolean(extras.isFollowing, false),
    ...extras
  })
}

/**
 * Normalize paginated response from API
 * @param {Object} result - Raw API response (already camelCase from interceptor)
 * @param {string} itemsKey - Key name for items in response (e.g., 'followers', 'following')
 * @param {number} defaultPage - Default page number
 * @param {number} defaultPageSize - Default page size
 * @returns {Object} Normalized pagination response
 */
function normalizePaginatedResponse(result, itemsKey, defaultPage = 1, defaultPageSize = DEFAULTS.PAGINATION.DEFAULT) {
  const normalized = normalizePeopleListResponse(result, itemsKey, {
    page: defaultPage,
    pageSize: defaultPageSize,
  })
  return {
    [itemsKey]: normalized[itemsKey],
    total: normalized.total,
    page: normalized.page,
    pageSize: normalized.pageSize
  }
}

// ============== User Profile ==============

/**
 * Get user profile
 * @param {string} userId - User ID
 * @returns {Promise<Object>} User profile
 */
export async function getUserProfile(userId) {
  const result = await get(ENDPOINTS.USERS.GET(userId) + '/profile')

  // Get follow status for non-self users
  const currentUserId = authAPI.getLocalUser()?.id
  let isFollowing = false

  if (currentUserId && currentUserId !== userId) {
    try {
      const followStatus = await get(`/users/follow/${userId}/status`)
      isFollowing = followStatus.isFollowing || false
    } catch {
      // Ignore errors checking follow status
    }
  }

  return normalizeUser(result, { isFollowing })
}

/**
 * Get user's public templates
 * @param {string} userId - User ID
 * @param {number} page - Page number
 * @param {number} pageSize - Page size
 * @returns {Promise<Object>} Templates list with pagination
 */
export async function getUserTemplates(userId, page = 1, pageSize = DEFAULTS.PAGINATION.DEFAULT) {
  // Templates are fetched via templates API with creator filter
  const result = await get(ENDPOINTS.TEMPLATES.LIST, {
    params: {
      creatorId: userId,
      visibility: 'public',
      page,
      pageSize
    }
  })

  // Handle both 'templates' and 'items' keys from API
  const normalized = normalizeCreatorTemplatesResponse(result, { page, pageSize })
  return {
    templates: normalized.templates,
    total: normalized.total,
    page: normalized.page,
    pageSize: normalized.pageSize
  }
}

// ============== Follow System ==============

/**
 * Follow a user
 * @param {string} userId - User to follow
 * @returns {Promise<Object>} Result
 */
export async function followUser(userId) {
  const currentUserId = getCurrentUserId()

  if (currentUserId === userId) {
    throw new Error(i18n.global.t('error.cannotFollowYourself'))
  }

  await post(ENDPOINTS.USERS.FOLLOW(userId))
  return { ok: true, message: i18n.global.t('message.followedUser') }
}

/**
 * Unfollow a user
 * @param {string} userId - User to unfollow
 * @returns {Promise<Object>} Result
 */
export async function unfollowUser(userId) {
  await del(ENDPOINTS.USERS.FOLLOW(userId))
  return { ok: true, message: i18n.global.t('message.unfollowedUser') }
}

/**
 * Get user's followers
 * @param {string} userId - User ID
 * @param {number} page - Page number
 * @param {number} pageSize - Page size
 * @returns {Promise<Object>} Followers list
 */
export async function getFollowers(userId, page = 1, pageSize = DEFAULTS.PAGINATION.DEFAULT) {
  const result = await get(`/users/${userId}/followers`, {
    params: { page, pageSize }
  })
  return normalizePaginatedResponse(result, 'followers', page, pageSize)
}

/**
 * Get users that a user is following
 * @param {string} userId - User ID
 * @param {number} page - Page number
 * @param {number} pageSize - Page size
 * @returns {Promise<Object>} Following list
 */
export async function getFollowing(userId, page = 1, pageSize = DEFAULTS.PAGINATION.DEFAULT) {
  const result = await get(`/users/${userId}/following`, {
    params: { page, pageSize }
  })
  return normalizePaginatedResponse(result, 'following', page, pageSize)
}

// ============== Notifications ==============

/**
 * Get user notifications
 * @param {number} page - Page number
 * @param {number} pageSize - Page size
 * @param {boolean} unreadOnly - Only unread notifications
 * @returns {Promise<Object>} Notifications list
 */
export async function getNotifications(page = 1, pageSize = DEFAULTS.PAGINATION.DEFAULT, unreadOnly = false) {
  const result = await get(ENDPOINTS.NOTIFICATIONS.LIST, {
    params: {
      page,
      pageSize,
      unreadOnly
    }
  })
  return normalizePaginatedResponse(result, 'notifications', page, pageSize)
}

/**
 * Delete a notification
 * @param {string} notificationId - Notification ID
 * @returns {Promise<Object>} Result
 */
export async function deleteNotification(notificationId) {
  await del(ENDPOINTS.NOTIFICATIONS.GET(notificationId))
  return { ok: true }
}

export default {
  getUserProfile,
  getUserTemplates,
  followUser,
  unfollowUser,
  getFollowers,
  getFollowing,
  getNotifications,
  deleteNotification
}
