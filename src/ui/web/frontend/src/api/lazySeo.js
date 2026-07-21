/**
 * Lazy SEO API
 * Automated SEO management with minimal effort
 */

import { get, post, del } from './client'

const BASE_URL = '/lazy-seo'

// =============================================================================
// Keywords
// =============================================================================

/**
 * List tracked keywords
 * @param {boolean|null} isTracked - Filter by tracked status
 * @param {string|null} source - Filter by source (manual, discovered, search_console)
 */
export async function listKeywords(isTracked = null, source = null) {
  const params = {}
  if (isTracked !== null) params.is_tracked = isTracked
  if (source) params.source = source
  return await get(`${BASE_URL}/keywords`, { params })
}

/**
 * Add a keyword to track
 * @param {string} keyword - The keyword to track
 * @param {string} location - Location (default: Taiwan)
 * @param {string} language - Language code (default: zh-TW)
 */
export async function addKeyword(keyword, location = 'Taiwan', language = 'zh-TW') {
  return await post(`${BASE_URL}/keywords`, { keyword, location, language })
}

/**
 * Remove a tracked keyword
 * @param {string} keywordId - Keyword ID
 */
export async function removeKeyword(keywordId) {
  return await del(`${BASE_URL}/keywords/${keywordId}`)
}

/**
 * Discover keywords from Search Console
 */
export async function discoverKeywords() {
  return await post(`${BASE_URL}/keywords/discover`)
}

export default {
  // Keywords
  listKeywords,
  addKeyword,
  removeKeyword,
  discoverKeywords,
}
