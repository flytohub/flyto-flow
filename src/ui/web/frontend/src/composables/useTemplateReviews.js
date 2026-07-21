/**
 * Template Reviews Composable
 * Handles review CRUD operations for templates
 */

import { ref } from 'vue'
import { templatesAPI } from '@/api/templates'
import { authAPI } from '@/api/auth'

/**
 * Create template reviews composable
 * @param {Object} options
 * @param {Function} options.onSuccess - Success callback
 * @param {Function} options.onError - Error callback
 * @returns {Object} Reviews state and methods
 */
export function useTemplateReviews(options = {}) {
  const { onSuccess, onError } = options

  // State
  const reviews = ref([])
  const reviewStats = ref({ total: 0 })
  const userReview = ref(null)
  const editingReview = ref(null)
  const reviewPage = ref(1)

  /**
   * Load reviews for a template
   */
  async function loadReviews(templateId) {
    if (!templateId) return

    try {
      const result = await templatesAPI.getReviews(templateId)
      if (result.ok) {
        reviews.value = result.reviews || []
        reviewStats.value = { total: reviews.value.length }

        const currentUser = authAPI.getLocalUser()
        if (currentUser) {
          userReview.value = reviews.value.find(r => r.userId === currentUser.uid) || null
        }
      }
    } catch (err) {
      onError?.(err)
    }
  }

  /**
   * Submit a new review
   */
  async function submitReview(templateId, data) {
    if (!templateId) return false

    try {
      const result = await templatesAPI.addReview(templateId, data.rating, data.comment)
      if (!result.ok) {
        throw new Error(result.error || 'Failed to submit review')
      }
      await loadReviews(templateId)
      onSuccess?.('Review submitted')
      return true
    } catch (err) {
      onError?.(err)
      return false
    }
  }

  /**
   * Update an existing review
   */
  async function updateReview(templateId, data) {
    if (!editingReview.value || !templateId) return false

    try {
      const result = await templatesAPI.updateReview(
        editingReview.value.id,
        data.rating,
        data.comment
      )
      if (!result.ok) {
        throw new Error(result.error || 'Failed to update review')
      }
      await loadReviews(templateId)
      editingReview.value = null
      onSuccess?.('Review updated')
      return true
    } catch (err) {
      onError?.(err)
      return false
    }
  }

  /**
   * Start editing a review
   */
  function startEditReview(review) {
    editingReview.value = review
  }

  /**
   * Cancel editing
   */
  function cancelEditReview() {
    editingReview.value = null
  }

  /**
   * Delete a review
   */
  async function deleteReview(reviewId) {
    try {
      const result = await templatesAPI.deleteReview(reviewId)
      if (!result.ok) {
        throw new Error(result.error || 'Failed to delete review')
      }
      reviews.value = reviews.value.filter(r => r.id !== reviewId)
      reviewStats.value.total--
      if (userReview.value?.id === reviewId) {
        userReview.value = null
      }
      onSuccess?.('Review deleted')
      return true
    } catch (err) {
      onError?.(err)
      return false
    }
  }

  /**
   * Mark review as helpful
   */
  async function markHelpful(reviewId) {
    // Not implemented yet
    return false
  }

  /**
   * Load more reviews
   */
  function loadMoreReviews(templateId) {
    reviewPage.value++
    loadReviews(templateId)
  }

  /**
   * Reset state
   */
  function reset() {
    reviews.value = []
    reviewStats.value = { total: 0 }
    userReview.value = null
    editingReview.value = null
    reviewPage.value = 1
  }

  return {
    // State
    reviews,
    reviewStats,
    userReview,
    editingReview,
    reviewPage,
    // Methods
    loadReviews,
    submitReview,
    updateReview,
    startEditReview,
    cancelEditReview,
    deleteReview,
    markHelpful,
    loadMoreReviews,
    reset
  }
}
