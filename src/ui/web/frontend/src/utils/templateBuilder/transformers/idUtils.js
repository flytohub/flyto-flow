/**
 * ID Utilities
 *
 * S-Grade: ID normalization and slug generation.
 * Single responsibility: Handle ID and slug transformations.
 */

/**
 * Normalize component ID (remove special characters, convert to lowercase)
 * @param {string} id - Original ID
 * @returns {string} Normalized ID
 */
export function normalizeComponentId(id) {
  if (!id || typeof id !== 'string') {
    return ''
  }

  return id
    .toLowerCase()
    .replace(/[^a-z0-9_-]/g, '_')
    .replace(/_{2,}/g, '_')
    .replace(/^_|_$/g, '')
}

/**
 * Generate slug (for URLs and IDs)
 * @param {string} text - Original text
 * @returns {string} Slug
 */
export function generateSlug(text) {
  if (!text || typeof text !== 'string') {
    return ''
  }

  return text
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '_')
    .replace(/[^a-z0-9_-]/g, '')
    .replace(/_{2,}/g, '_')
    .replace(/^_|_$/g, '')
}
