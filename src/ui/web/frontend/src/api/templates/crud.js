/** Local CE template CRUD. */
import { get, post, put, del } from '@/api/client'
import { normalizeTemplate } from './helpers'

function payload(data) {
  return {
    name: data.templateName || data.name || 'Untitled workflow',
    description: data.templateDescription || data.description || '',
    category: data.categoryId || data.category || 'general',
    tags: data.tags || [],
    steps: data.steps || data.workflowSteps || [],
    ui: data.ui || null,
    params_schema: data.paramsSchema || data.params_schema || {},
    color: data.color || null,
    checkpoints: data.checkpoints || [],
    error_workflow_id: data.errorWorkflowId || data.error_workflow_id || null,
    error_handling: data.errorHandling || data.error_handling || null,
  }
}

export async function createTemplate(data) {
  try {
    const result = await post('/templates/', payload(data))
    return result.ok
      ? { ok: true, template: normalizeTemplate(result.template) }
      : { ok: false, error: result.error || 'Failed to create workflow' }
  } catch (error) {
    return { ok: false, error: error.message }
  }
}

export async function updateTemplate(id, data) {
  try {
    const result = await put(`/templates/${encodeURIComponent(id)}`, payload(data))
    return result.ok
      ? { ok: true, template: normalizeTemplate(result.template, id) }
      : { ok: false, error: result.error || 'Failed to update workflow' }
  } catch (error) {
    return { ok: false, error: error.message }
  }
}

export async function getTemplate(id) {
  try {
    const result = await get(`/templates/${encodeURIComponent(id)}`)
    return result.ok
      ? { ok: true, template: normalizeTemplate(result.template, id) }
      : { ok: false, error: result.error || 'Workflow not found' }
  } catch (error) {
    return { ok: false, error: error.message }
  }
}

export async function listTemplates({ page = 1, pageSize = 200 } = {}) {
  try {
    const result = await get('/templates/', { params: { page, page_size: pageSize } })
    const items = result.items || result.templates || []
    return {
      ok: result.ok !== false,
      templates: items.map(item => normalizeTemplate(item)),
      total: result.total ?? items.length,
    }
  } catch (error) {
    return { ok: false, error: error.message, templates: [], total: 0 }
  }
}

export async function deleteTemplate(id) {
  try {
    await del(`/templates/${encodeURIComponent(id)}`)
    return { ok: true }
  } catch (error) {
    return { ok: false, error: error.message }
  }
}
