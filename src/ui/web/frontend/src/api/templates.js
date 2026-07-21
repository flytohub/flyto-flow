/**
 * Templates API
 *
 * This file re-exports from the modular templates/ directory
 * for backward compatibility.
 *
 * New code should import directly from specific modules:
 *   import { createTemplate } from '@/api/templates/crud'
 *   import { getLibrary } from '@/api/templates/library'
 *
 * Or use the unified API:
 *   import { templatesAPI } from '@/api/templates'
 */

export {
  templatesAPI,
  normalizeTemplate,
  getCurrentUserId,
  getCurrentUser,
  crud,
  library,
  reviews,
  inviteKeys,
  purchases,
  categories
} from './templates/index'

// Direct named exports for common operations
export { listTemplates } from './templates/crud'

export { default } from './templates/index'
