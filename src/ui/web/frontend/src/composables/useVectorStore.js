/**
 * Vector Store Composable
 *
 * Encapsulates vector store API calls for collection management.
 * Eliminates direct fetch() calls in components.
 */

import { ref, readonly } from 'vue'
import { get, post, del } from '@/api/client'

/**
 * Vector Store API composable
 *
 * @returns {Object} Vector store state and actions
 *
 * @example
 * const { collections, loading, error, loadCollections, createCollection } = useVectorStore()
 * await loadCollections()
 * await createCollection('my_collection')
 */
export function useVectorStore() {
  // State
  const collections = ref([])
  const loading = ref(false)
  const error = ref(null)

  /**
   * Load all collections from API
   *
   * @returns {Promise<Array>} Collections list
   */
  async function loadCollections() {
    loading.value = true
    error.value = null

    try {
      const data = await get('/vector/collections')
      collections.value = data.collections || []
      return collections.value
    } catch (err) {
      error.value = err.message || 'Failed to load collections'
      // Fallback to default collection
      collections.value = [{ name: 'flyto_knowledge', count: 0 }]
      return collections.value
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new collection
   *
   * @param {string} name - Collection name
   * @returns {Promise<Object|null>} Created collection or null on error
   */
  async function createCollection(name) {
    if (!name || !name.trim()) {
      error.value = 'Collection name is required'
      return null
    }

    loading.value = true
    error.value = null

    try {
      const data = await post('/vector/collections', { name: name.trim() })
      // Refresh collections list after creation
      await loadCollections()
      return data
    } catch (err) {
      error.value = err.message || 'Failed to create collection'
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete a collection
   *
   * @param {string} name - Collection name to delete
   * @returns {Promise<boolean>} Success status
   */
  async function deleteCollection(name) {
    if (!name) {
      error.value = 'Collection name is required'
      return false
    }

    loading.value = true
    error.value = null

    try {
      await del(`/vector/collections/${encodeURIComponent(name)}`)
      // Refresh collections list after deletion
      await loadCollections()
      return true
    } catch (err) {
      error.value = err.message || 'Failed to delete collection'
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear error state
   */
  function clearError() {
    error.value = null
  }

  /**
   * Get collection by name
   *
   * @param {string} name - Collection name
   * @returns {Object|undefined} Collection object or undefined
   */
  function getCollection(name) {
    return collections.value.find(c => c.name === name)
  }

  return {
    // State (readonly for safety)
    collections: readonly(collections),
    loading: readonly(loading),
    error: readonly(error),

    // Actions
    loadCollections,
    createCollection,
    deleteCollection,
    clearError,
    getCollection
  }
}

export default useVectorStore
