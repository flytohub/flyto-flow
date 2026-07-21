/**
 * Templates API - Category Operations
 * Uses Gateway API instead of Firebase SDK
 */

import { get } from '@/api/client'
import { ENDPOINTS } from '@/api/config'
import i18n from '@/i18n'

// Default categories when none exist in API
function getDefaultCategories() {
  const t = i18n.global.t
  return [
    { id: 'automation', slug: 'automation', name: t('templateCategory.automation'), icon: 'zap' },
    { id: 'data', slug: 'data', name: t('templateCategory.dataProcessing'), icon: 'database' },
    { id: 'web', slug: 'web', name: t('templateCategory.webScraping'), icon: 'globe' },
    { id: 'social', slug: 'social', name: t('templateCategory.socialMedia'), icon: 'share-2' },
    { id: 'productivity', slug: 'productivity', name: t('templateCategory.productivity'), icon: 'briefcase' },
    { id: 'other', slug: 'other', name: t('toolCategory.other'), icon: 'folder' }
  ]
}

// Slug to i18n key mapping (for legacy slugs that don't match i18n keys)
const SLUG_TO_KEY = {
  'automation': 'automation',
  'data': 'dataProcessing',
  'data-processing': 'dataProcessing',
  'web': 'webScraping',
  'web-scraping': 'webScraping',
  'browser': 'webScraping',
  'social': 'socialMedia',
  'social-media': 'socialMedia',
  'productivity': 'productivity',
  'api': 'api',
  'api-integration': 'api',
  'image': 'image',
  'image-media': 'image',
  'notification': 'notification',
  'notification-bot': 'notification',
  'media': 'media',
  'ai': 'ai',
  'ai-utility': 'ai',
  'file': 'file',
  'file-csv-excel': 'file',
  'monitoring': 'monitoring',
  'developer': 'developer',
  'developer-tools': 'developer',
  'devtools': 'developer',
  'other': 'other'
}

/**
 * Get localized category name using i18n
 * Key format: templateCategory.{mappedKey}
 * Falls back to slug if translation not found
 */
function getLocalizedName(slug) {
  const t = i18n.global.t
  // Map slug to i18n key, fallback to slug itself
  const mappedKey = SLUG_TO_KEY[slug] || slug
  const key = `templateCategory.${mappedKey}`
  const translated = t(key)
  // If translation returns the key itself, try toolCategory as fallback
  if (translated === key) {
    const fallbackKey = `toolCategory.${mappedKey}`
    const fallback = t(fallbackKey)
    return fallback === fallbackKey ? slug : fallback
  }
  return translated
}

/**
 * Get all categories
 */
export async function getCategories() {
  try {
    const result = await get(ENDPOINTS.TEMPLATES.CATEGORIES)

    if (!result.ok || !result.categories || result.categories.length === 0) {
      return { ok: true, categories: getDefaultCategories() }
    }

    // Normalize API response with i18n localized name
    const categories = result.categories.map(cat => ({
      id: cat.id || cat.slug,
      name: getLocalizedName(cat.slug),
      slug: cat.slug,
      icon: cat.icon,
      templateCount: cat.templateCount || 0
    }))

    return { ok: true, categories }
  } catch (err) {
    // Return defaults on error
    return { ok: true, categories: getDefaultCategories() }
  }
}
