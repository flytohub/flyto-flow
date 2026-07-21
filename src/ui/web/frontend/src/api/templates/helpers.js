/**
 * Templates API - Shared Helpers
 */

import i18n from '@/i18n'

// Re-export auth utilities for backward compatibility
export { getCurrentUserId, getCurrentUser } from '@/utils/auth'

/**
 * Resolve a translated field from template translations.
 * Falls back to the original value if no translation exists.
 */
export function resolveTranslated(translations, locale, field, fallback) {
  if (!translations || !locale) return fallback
  const t = translations[locale]
  if (t && t[field]) return t[field]
  return fallback
}

/**
 * Get the current i18n locale
 */
export function getCurrentLocale() {
  return i18n.global.locale?.value || i18n.global.locale || 'en'
}

/**
 * Normalize template data to a consistent format
 * This ensures all API functions return the same structure
 *
 * NOTE: name/description are always the ORIGINAL (untranslated) values.
 * Use resolveTranslated() at the display layer for i18n.
 */
export function normalizeTemplate(data, docId = null) {
  const id = docId || data.id

  // Read from camelCase (client.js converts snake_case to camelCase)
  const name = data.templateName || data.name || 'Untitled'
  const description = data.templateDescription || data.description || ''
  const status = data.templateStatus || data.status || 'draft'
  const category = data.categoryId || data.category || 'other'
  const pricing = data.pricing || 'free'

  // Handle date fields (could be Firestore Timestamp, ISO string, or Date)
  const parseDate = (dateField) => {
    if (!dateField) return null
    if (typeof dateField === 'string') return dateField
    if (dateField?.toDate) return dateField.toDate().toISOString()
    if (dateField instanceof Date) return dateField.toISOString()
    return null
  }

  return {
    id,
    // Unified field names (camelCase only - trust the converter)
    name,
    description,
    status,
    category,
    // Backward compatibility aliases (DEPRECATED - use name/description/status instead)
    templateName: name,
    templateDescription: description,
    templateStatus: status,
    categoryId: category,
    categorySlug: category,
    // Pricing
    pricing,
    price: data.price || 0,
    callPrice: data.callPrice || null,
    // Creator info (camelCase)
    creatorId: data.creatorId,
    creatorName: data.creatorName || data.creatorEmail?.split('@')[0] || 'Anonymous',
    creatorEmail: data.creatorEmail,
    // Stats (camelCase)
    downloads: data.downloadCount || data.downloads || 0,
    rating: data.ratingCount > 0 ? (data.ratingSum / data.ratingCount) : 0,
    ratingSum: data.ratingSum || 0,
    ratingCount: data.ratingCount || 0,
    // Visual (camelCase - trust the converter)
    iconUrl: data.iconUrl || data.templateIcon,
    tags: data.tags || [],
    // Workflow data
    steps: data.steps || data.workflowSteps || data.workflow?.steps || [],
    ui: data.ui,
    // Visibility & publishing (camelCase)
    visibility: data.visibility || 'private',
    listed: data.marketplaceStatus ? data.marketplaceStatus === 'visible' : true,
    marketplaceStatus: data.marketplaceStatus || 'visible',
    isVerified: data.isVerified || false,
    isFeatured: data.isFeatured || false,
    // Workflow protection (from backend - determines if non-owner can see workflow)
    mutability: data.mutability || 'fork_on_use',
    is_workflow_visible: data.isWorkflowVisible !== false,  // Backend sets this based on ownership + mutability
    // Dates (camelCase)
    createdAt: parseDate(data.createdAt) || parseDate(data.addedAt),
    updatedAt: parseDate(data.updatedAt),
    // User-specific (camelCase)
    isInstalled: data.isInstalled || false,
    hasAccess: data.hasAccess || false,
    // Action flags (computed by backend enrichment)
    isOwnTemplate: data.isOwnTemplate || false,
    isPerCall: data.isPerCall || false,
    isPaidWithoutAccess: data.isPaidWithoutAccess || false,
    source: data.source,
    entitlement: data.entitlement,
    // Revision & versioning
    revision: data.revision || null,
    version: data.version || null,
    // Additional fields
    color: data.color || null,
    executionCount: data.execution_count || data.executionCount || 0,
    capabilities: data.capabilities || null,
    hasPendingChanges: data.has_pending_changes || data.hasPendingChanges || false,
    forkCount: data.fork_count || data.forkCount || 0,
    defaultLanguage: data.default_language || data.defaultLanguage || null,
    translations: data.translations || null,
    // Collaboration
    contributors: data.contributors || [],
    contributorCount: data.contributor_count || data.contributorCount || 0,
    openPrCount: data.open_pr_count || data.openPrCount || 0,
    openIssueCount: data.open_issue_count || data.openIssueCount || 0,
    isCollaborator: data.isCollaborator || data.is_collaborator || false,
    // Rich content
    videoUrl: data.videoUrl || data.video_url || null,
    usageInstructions: data.usageInstructions || data.usage_instructions || null,
    screenshots: data.screenshots || [],
    // Folder
    folder_id: data.folderId || data.folder_id || null,
  }
}

