/**
 * Templates API - CRUD Operations
 * Uses Gateway API instead of Firebase SDK
 */

import { get, post, patch, put, del } from '@/api/client'
import { ENDPOINTS } from '@/api/config'
import { normalizeTemplate, getCurrentUserId, getCurrentUser } from './helpers'
import i18n from '@/i18n'
import { asObject, asRecordArray, asNonNegativeInteger } from '@/utils/dataBoundary'

/**
 * Create new template
 */
export async function createTemplate(templateData) {
  try {
    const user = getCurrentUser()

    const result = await post(ENDPOINTS.TEMPLATES.CREATE, {
      name: templateData.templateName || templateData.name,
      description: templateData.templateDescription || templateData.description,
      category: templateData.categoryId || templateData.category || 'other',
      visibility: templateData.visibility || 'private',
      pricing: templateData.pricing || 'free',
      price: templateData.price || 0,
      tags: templateData.tags || [],
      steps: templateData.steps || templateData.workflowSteps || [],
      ui: templateData.ui,
      iconUrl: templateData.iconUrl,
      error_workflow_id: templateData.error_workflow_id || undefined,
      error_handling: templateData.error_handling || undefined,
      checkpoints: templateData.checkpoints || undefined,
      folder_id: templateData.folder_id || templateData.folderId || undefined,
    })

    if (!result.ok) {
      return { ok: false, error: result.error || i18n.global.t('error.failedToCreateTemplate') }
    }

    return {
      ok: true,
      template: {
        ...result.template,
        id: result.template?.id,
        creatorId: user.uid,
        creatorEmail: user.email
      }
    }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Update template
 */
export async function updateTemplate(templateId, templateData) {
  try {
    const result = await patch(ENDPOINTS.TEMPLATES.UPDATE(templateId), {
      name: templateData.templateName || templateData.name,
      description: templateData.templateDescription || templateData.description,
      category: templateData.categoryId || templateData.category,
      visibility: templateData.visibility,
      pricing: templateData.pricing,
      price: templateData.price,
      tags: templateData.tags,
      steps: templateData.steps || templateData.workflowSteps,
      ui: templateData.ui,
      iconUrl: templateData.iconUrl,
      color: templateData.color,
      status: templateData.templateStatus || templateData.status,
      listed: templateData.listed,
      mutability: templateData.mutability,
      expected_revision: templateData.revision || templateData.expectedRevision,
      change_summary: templateData.changeSummary,
      error_workflow_id: templateData.error_workflow_id,
      error_handling: templateData.error_handling,
      checkpoints: templateData.checkpoints,
      // i18n
      default_language: templateData.defaultLanguage,
      translations: templateData.translations,
      // Rich content
      video_url: templateData.videoUrl,
      usage_instructions: templateData.usageInstructions,
      // Regional visibility
      visibility_regions: templateData.visibilityRegions,
      blocked_regions: templateData.blockedRegions,
      // Pricing
      call_price: templateData.callPrice,
      currency: templateData.currency,
    })

    if (!result.ok) {
      return { ok: false, error: result.error || i18n.global.t('error.failedToUpdateTemplate') }
    }

    return { ok: true, template: result.template }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Get template by ID
 * Also checks if current user has access (purchased, owns, or free template)
 */
export async function getTemplate(templateId) {
  try {
    const result = await get(ENDPOINTS.TEMPLATES.GET(templateId))

    if (!result.ok) {
      return { ok: false, error: result.error || i18n.global.t('error.templateNotFound') }
    }

    const template = normalizeTemplate(result.template, templateId)

    // Trust backend access decisions
    template.hasAccess = result.template.hasAccess ?? (result.template.capabilities?.canExecute ?? false)
    template.isInstalled = result.template.isInstalled ?? false

    return { ok: true, template }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * List templates
 * For creator_id: returns all templates owned by user
 * For marketplace: returns published templates
 */
/**
 * S-Grade: Supports server-side enabled filtering via query param.
 */
export async function listTemplates(params = {}) {
  try {
    const { category, creatorId, pageSize = 100, enabled, search, sortBy, status } = params

    const queryParams = {
      pageSize
    }

    if (creatorId) {
      queryParams.creatorId = creatorId
    }

    if (category) {
      queryParams.category = category
    }

    // S-Grade: Server-side enabled filtering
    if (enabled !== undefined) {
      queryParams.enabled = enabled
    }

    // MyTemplates: Server-side search/sort/status
    if (search) queryParams.search = search
    if (sortBy) queryParams.sort_by = sortBy
    if (status) queryParams.status = status

    const result = await get(ENDPOINTS.TEMPLATES.LIST, { params: queryParams })

    if (!result.ok) {
      return { ok: false, error: result.error, templates: [] }
    }

    const templates = (result.templates || []).map(t => normalizeTemplate(t, t.id))

    return {
      ok: true,
      templates,
      total: templates.length,
      // S-Grade: Backend-computed counts
      enabledCount: result.enabledCount,
      totalCount: result.totalCount,
      // MyTemplates: Status counts
      draftCount: result.draftCount,
      publishedCount: result.publishedCount
    }
  } catch (err) {
    return { ok: false, error: err.message, templates: [] }
  }
}

/**
 * List current user's own templates with server-side search/sort/filter
 * Uses GET /me/templates (enhanced endpoint with stats)
 */
export async function listMyTemplates(params = {}) {
  try {
    const { search, sortBy, status, pageSize = 50, page = 1, folderId } = params

    const queryParams = { page_size: pageSize, page }
    if (search) queryParams.search = search
    if (sortBy) queryParams.sort_by = sortBy
    if (status) queryParams.status = status
    if (folderId !== undefined && folderId !== null) queryParams.folder_id = folderId

    const result = asObject(await get('/templates/me/templates', { params: queryParams }))

    if (!result.ok) {
      return { ok: false, error: result.error, templates: [] }
    }

    const templates = asRecordArray(result.templates).map(t => normalizeTemplate(t, t.id))
    const total = asNonNegativeInteger(result.total, templates.length)

    return {
      ok: true,
      templates,
      total,
      page,
      pageSize,
      hasNext: (page * pageSize) < total,
      draftCount: asNonNegativeInteger(result.draftCount ?? result.draft_count, 0),
      publishedCount: asNonNegativeInteger(result.publishedCount ?? result.published_count, 0)
    }
  } catch (err) {
    return { ok: false, error: err.message, templates: [] }
  }
}

/**
 * Batch delete templates (parallel on backend)
 */
export async function batchDeleteTemplates(templateIds) {
  try {
    const result = await post('/templates/me/batch-delete', { template_ids: templateIds })
    return { ok: true, deleted: result.deleted, failed: result.failed }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Delete template
 */
export async function deleteTemplate(templateId) {
  try {
    await del(ENDPOINTS.TEMPLATES.DELETE(templateId))
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Search templates (marketplace)
 * Returns published templates with user access status.
 * Supports server-side filtering and sorting via query params.
 *
 * @param {Object} params
 * @param {string}  [params.search]   - Text search query
 * @param {string}  [params.category] - Category slug/ID filter
 * @param {string}  [params.pricing]  - Pricing filter: free | paid | per_call
 * @param {string}  [params.sortBy]   - Sort: downloads | rating | created_at | name
 * @param {number}  [params.pageSize] - Page size (default 100)
 * @param {number}  [params.page]     - Page number (default 1)
 */
export async function searchTemplates(params = {}) {
  try {
    const { search, category, pricing, sortBy, pageSize = 100, page } = params

    const queryParams = {
      page_size: pageSize
    }

    if (search) {
      queryParams.q = search
    }

    if (category) {
      queryParams.category = category
    }

    if (pricing && pricing !== 'all') {
      queryParams.pricing = pricing
    }

    if (sortBy) {
      // Map frontend sort names to backend parameter values
      const sortMap = { popular: 'downloads', newest: 'created_at', rating: 'rating', name: 'name' }
      queryParams.sort_by = sortMap[sortBy] || sortBy
    }

    if (page && page > 1) {
      queryParams.page = page
    }

    const result = asObject(await get(ENDPOINTS.TEMPLATES.SEARCH, { params: queryParams }))

    if (!result.ok) {
      return { ok: false, error: result.error, templates: [] }
    }

    const templates = asRecordArray(result.templates).map(t => normalizeTemplate(t, t.id))

    return { ok: true, templates, total: asNonNegativeInteger(result.total, templates.length) }
  } catch (err) {
    return { ok: false, error: err.message, templates: [] }
  }
}

/**
 * Unpublish template from marketplace.
 * Uses the dedicated POST /unpublish endpoint which:
 * - Sets visibility to private, marketplace_status to hidden
 * - Marks all purchases as source_unpublished
 * - Deactivates all invite keys
 */
export async function unpublishTemplate(templateId) {
  try {
    const result = await post(`/templates/${templateId}/unpublish`)
    if (!result.ok) {
      return { ok: false, error: result.error || 'Failed to unpublish template' }
    }
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Update marketplace listing snapshot from current live template
 */
export async function updateMarketplaceListing(templateId) {
  try {
    const result = await post(`/templates/${templateId}/update-marketplace`)
    if (!result.ok) {
      return { ok: false, error: result.error || 'Failed to update marketplace listing' }
    }
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Execute template - calls Python backend
 * For locked templates, this allows execution without exposing workflow to frontend
 */
export async function executeTemplate(templateId, inputParams = {}) {
  try {
    // Backend expects entire body to be the input_params dict
    // FastAPI parses: input_params: dict = body
    const result = await post(ENDPOINTS.TEMPLATES.EXECUTE(templateId), inputParams)
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

// =============================================================================
// YAML Export / Import
// =============================================================================

/**
 * Export template as unified YAML
 * Returns { ok, yaml, filename }
 */
export async function exportYAML(templateId) {
  try {
    const result = await get(`/templates/${templateId}/export`)
    if (!result.ok) {
      return { ok: false, error: result.error || 'Export failed' }
    }
    return { ok: true, yaml: result.yaml, filename: result.filename }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Import a YAML string to create a new template
 */
export async function importYAML(yamlContent) {
  try {
    const result = await post('/templates/import/yaml', {
      yaml_content: yamlContent
    })
    if (!result.ok) {
      return { ok: false, error: result.error || 'Failed to import YAML' }
    }
    return {
      ok: true,
      template: result.template,
      needsAutoLayout: result.needs_auto_layout
    }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Push YAML update to an existing template (creates new version or PR)
 * @param {string} templateId
 * @param {string} yamlContent
 * @param {Object} options - { changeSummary, createPR, prTitle }
 * @returns { ok, action: 'updated'|'pr_created', template?, pullRequest?, needsAutoLayout }
 */
export async function pushYAML(templateId, yamlContent, options = {}) {
  try {
    const { changeSummary = '', createPR, prTitle } = typeof options === 'string'
      ? { changeSummary: options }  // backward compat: pushYAML(id, yaml, 'summary')
      : options

    const result = await put(`/templates/${templateId}/push`, {
      yaml_content: yamlContent,
      change_summary: changeSummary,
      create_pr: createPR ?? undefined,
      pr_title: prTitle ?? undefined,
    })
    if (!result.ok) {
      return { ok: false, error: result.error || 'Failed to push YAML' }
    }
    return {
      ok: true,
      action: result.action,
      template: result.template,
      pullRequest: result.pull_request,
      needsAutoLayout: result.needs_auto_layout
    }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Pull latest template version as YAML (with full secrets for owner)
 */
export async function pullYAML(templateId) {
  try {
    const result = await get(`/templates/${templateId}/pull`)
    if (!result.ok) {
      return { ok: false, error: result.error || 'Pull failed' }
    }
    return {
      ok: true,
      yaml: result.yaml,
      filename: result.filename,
      versionNumber: result.version_number,
      templateId: result.template_id,
    }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Compare proposed YAML against current template
 */
export async function diffYAML(templateId, yamlContent) {
  try {
    const result = await post(`/templates/${templateId}/diff`, {
      yaml_content: yamlContent
    })
    if (!result.ok) {
      return { ok: false, error: result.error || 'Diff failed' }
    }
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Compare two template versions as YAML diff
 */
export async function diffVersionsYAML(templateId, versionA, versionB) {
  try {
    const result = await get(`/templates/${templateId}/versions/${versionA}/diff/${versionB}`)
    if (!result.ok) {
      return { ok: false, error: result.error || 'Diff failed' }
    }
    return { ok: true, ...result }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Get available tags across all user's templates
 * @returns {Promise<string[]>}
 */
export async function getAvailableTags() {
  try {
    const result = await get(ENDPOINTS.TEMPLATES.AVAILABLE_TAGS)
    return result.tags ?? []
  } catch (err) {
    console.error('Failed to fetch available tags:', err)
    return []
  }
}
