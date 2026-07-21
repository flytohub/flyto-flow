/**
 * Templates API - Review Operations
 * Uses Gateway API instead of Firebase SDK
 */

import { get, post, put, del } from '@/api/client'
import i18n from '@/i18n'

/**
 * Get reviews for a template
 */
export async function getReviews(templateId) {
  try {
    const result = await get(`/templates/${templateId}/reviews`)

    return {
      ok: true,
      reviews: result.reviews || []
    }
  } catch (err) {
    return { ok: false, error: err.message, reviews: [] }
  }
}

/**
 * Add review
 */
export async function addReview(templateId, rating, comment = '') {
  try {
    const result = await post(`/templates/${templateId}/reviews`, {
      rating,
      comment
    })

    if (!result.ok) {
      return { ok: false, error: result.error || i18n.global.t('error.failedToAddReview') }
    }

    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Update an existing review
 */
export async function updateReview(reviewId, rating, comment = '') {
  try {
    const result = await put(`/templates/reviews/${reviewId}`, {
      rating,
      comment
    })

    if (!result.ok) {
      return { ok: false, error: result.error || i18n.global.t('error.failedToAddReview') }
    }

    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Delete review
 */
export async function deleteReview(reviewId) {
  try {
    await del(`/templates/reviews/${reviewId}`)
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}
