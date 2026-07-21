import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/client', () => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  put: vi.fn(),
  del: vi.fn()
}))

vi.mock('@/api/config', () => ({
  ENDPOINTS: {
    TEMPLATES: {
      LIST: '/templates/',
      GET: (id) => `/templates/${id}`,
      CREATE: '/templates/',
      UPDATE: (id) => `/templates/${id}`,
      DELETE: (id) => `/templates/${id}`,
      EXECUTE: (id) => `/templates/${id}/execute`,
      SEARCH: '/templates/search',
      AVAILABLE_TAGS: '/templates/available-tags'
    }
  }
}))

vi.mock('@/api/templates/helpers', () => ({
  normalizeTemplate: vi.fn((t, id) => ({ ...t, id: id || t.id, _normalized: true })),
  getCurrentUserId: vi.fn(() => 'user-1'),
  getCurrentUser: vi.fn(() => ({ uid: 'user-1', email: 'u@flyto2.com' }))
}))

vi.mock('@/i18n', () => ({
  default: {
    global: {
      t: vi.fn((key) => key)
    }
  }
}))

import { get, post, patch, put, del } from '@/api/client'
import {
  createTemplate,
  updateTemplate,
  getTemplate,
  listTemplates,
  listMyTemplates,
  deleteTemplate,
  searchTemplates,
  executeTemplate,
  exportYAML,
  importYAML,
  pushYAML,
  pullYAML,
  diffYAML,
  unpublishTemplate,
  getAvailableTags,
  batchDeleteTemplates
} from '@/api/templates/crud'

describe('Templates CRUD API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // =========================================================================
  // createTemplate
  // =========================================================================

  describe('createTemplate()', () => {
    it('calls POST /templates/ with template data', async () => {
      post.mockResolvedValue({ ok: true, template: { id: 't1', name: 'Test' } })

      const result = await createTemplate({ name: 'Test', description: 'Desc' })

      expect(post).toHaveBeenCalledWith('/templates/', expect.objectContaining({
        name: 'Test',
        description: 'Desc'
      }))
      expect(result.ok).toBe(true)
      expect(result.template.id).toBe('t1')
    })

    it('defaults category to other and visibility to private', async () => {
      post.mockResolvedValue({ ok: true, template: { id: 't1' } })

      await createTemplate({ name: 'Test' })

      const payload = post.mock.calls[0][1]
      expect(payload.category).toBe('other')
      expect(payload.visibility).toBe('private')
    })

    it('returns error when response.ok is false', async () => {
      post.mockResolvedValue({ ok: false, error: 'Duplicate name' })

      const result = await createTemplate({ name: 'Dup' })

      expect(result.ok).toBe(false)
      expect(result.error).toBe('Duplicate name')
    })

    it('handles API errors gracefully', async () => {
      post.mockRejectedValue(new Error('Server Error'))

      const result = await createTemplate({ name: 'Fail' })

      expect(result.ok).toBe(false)
      expect(result.error).toBe('Server Error')
    })
  })

  // =========================================================================
  // updateTemplate
  // =========================================================================

  describe('updateTemplate()', () => {
    it('calls PATCH /templates/:id with update data', async () => {
      patch.mockResolvedValue({ ok: true, template: { id: 't1', name: 'Updated' } })

      const result = await updateTemplate('t1', { name: 'Updated' })

      expect(patch).toHaveBeenCalledWith('/templates/t1', expect.objectContaining({
        name: 'Updated'
      }))
      expect(result.ok).toBe(true)
    })

    it('returns error on failure', async () => {
      patch.mockResolvedValue({ ok: false, error: 'Conflict' })

      const result = await updateTemplate('t1', {})

      expect(result.ok).toBe(false)
      expect(result.error).toBe('Conflict')
    })
  })

  // =========================================================================
  // getTemplate
  // =========================================================================

  describe('getTemplate()', () => {
    it('calls GET /templates/:id and normalizes result', async () => {
      get.mockResolvedValue({
        ok: true,
        template: {
          id: 't1',
          name: 'Test',
          hasAccess: true,
          isInstalled: false
        }
      })

      const result = await getTemplate('t1')

      expect(get).toHaveBeenCalledWith('/templates/t1')
      expect(result.ok).toBe(true)
      expect(result.template._normalized).toBe(true)
      expect(result.template.hasAccess).toBe(true)
    })

    it('returns error if not ok', async () => {
      get.mockResolvedValue({ ok: false, error: 'Not found' })

      const result = await getTemplate('bad-id')

      expect(result.ok).toBe(false)
    })
  })

  // =========================================================================
  // listTemplates
  // =========================================================================

  describe('listTemplates()', () => {
    it('calls GET /templates/ with default pageSize', async () => {
      get.mockResolvedValue({ ok: true, templates: [{ id: 't1' }] })

      const result = await listTemplates()

      expect(get).toHaveBeenCalledWith('/templates/', {
        params: expect.objectContaining({ pageSize: 100 })
      })
      expect(result.ok).toBe(true)
      expect(result.templates).toHaveLength(1)
    })

    it('passes category and creatorId filters', async () => {
      get.mockResolvedValue({ ok: true, templates: [] })

      await listTemplates({ category: 'browser', creatorId: 'user-1' })

      const params = get.mock.calls[0][1].params
      expect(params.category).toBe('browser')
      expect(params.creatorId).toBe('user-1')
    })

    it('passes enabled filter for S-Grade filtering', async () => {
      get.mockResolvedValue({ ok: true, templates: [] })

      await listTemplates({ enabled: true })

      const params = get.mock.calls[0][1].params
      expect(params.enabled).toBe(true)
    })

    it('passes search, sortBy, status params', async () => {
      get.mockResolvedValue({ ok: true, templates: [] })

      await listTemplates({ search: 'test', sortBy: 'created_at', status: 'published' })

      const params = get.mock.calls[0][1].params
      expect(params.search).toBe('test')
      expect(params.sort_by).toBe('created_at')
      expect(params.status).toBe('published')
    })

    it('returns enabledCount and totalCount from backend', async () => {
      get.mockResolvedValue({
        ok: true,
        templates: [],
        enabledCount: 5,
        totalCount: 10,
        draftCount: 3,
        publishedCount: 7
      })

      const result = await listTemplates()

      expect(result.enabledCount).toBe(5)
      expect(result.totalCount).toBe(10)
    })
  })

  // =========================================================================
  // listMyTemplates
  // =========================================================================

  describe('listMyTemplates()', () => {
    it('calls GET /templates/me/templates', async () => {
      get.mockResolvedValue({ ok: true, templates: [], total: 0 })

      await listMyTemplates()

      expect(get).toHaveBeenCalledWith('/templates/me/templates', {
        params: expect.objectContaining({ page_size: 50, page: 1 })
      })
    })

    it('passes search, sortBy, status filters', async () => {
      get.mockResolvedValue({ ok: true, templates: [] })

      await listMyTemplates({ search: 'hello', sortBy: 'name', status: 'draft' })

      const params = get.mock.calls[0][1].params
      expect(params.search).toBe('hello')
      expect(params.sort_by).toBe('name')
      expect(params.status).toBe('draft')
    })
  })

  // =========================================================================
  // deleteTemplate
  // =========================================================================

  describe('deleteTemplate()', () => {
    it('calls DELETE /templates/:id', async () => {
      del.mockResolvedValue({})

      const result = await deleteTemplate('t1')

      expect(del).toHaveBeenCalledWith('/templates/t1')
      expect(result.ok).toBe(true)
    })

    it('returns error on failure', async () => {
      del.mockRejectedValue(new Error('Forbidden'))

      const result = await deleteTemplate('t1')

      expect(result.ok).toBe(false)
      expect(result.error).toBe('Forbidden')
    })
  })

  // =========================================================================
  // batchDeleteTemplates
  // =========================================================================

  describe('batchDeleteTemplates()', () => {
    it('calls POST /templates/me/batch-delete with template_ids', async () => {
      post.mockResolvedValue({ deleted: ['t1', 't2'], failed: [] })

      const result = await batchDeleteTemplates(['t1', 't2'])

      expect(post).toHaveBeenCalledWith('/templates/me/batch-delete', { template_ids: ['t1', 't2'] })
      expect(result.ok).toBe(true)
      expect(result.deleted).toEqual(['t1', 't2'])
    })
  })

  // =========================================================================
  // searchTemplates
  // =========================================================================

  describe('searchTemplates()', () => {
    it('calls GET /templates/search with query params', async () => {
      get.mockResolvedValue({ ok: true, templates: [{ id: 't1' }], total: 1 })

      const result = await searchTemplates({ search: 'browser', category: 'automation' })

      expect(get).toHaveBeenCalledWith('/templates/search', {
        params: expect.objectContaining({
          q: 'browser',
          category: 'automation',
          page_size: 100
        })
      })
      expect(result.ok).toBe(true)
    })

    it('maps frontend sort names to backend values', async () => {
      get.mockResolvedValue({ ok: true, templates: [] })

      await searchTemplates({ sortBy: 'popular' })

      const params = get.mock.calls[0][1].params
      expect(params.sort_by).toBe('downloads')
    })

    it('does not include pricing when set to "all"', async () => {
      get.mockResolvedValue({ ok: true, templates: [] })

      await searchTemplates({ pricing: 'all' })

      const params = get.mock.calls[0][1].params
      expect(params.pricing).toBeUndefined()
    })

    it('includes pricing when set to "free" or "paid"', async () => {
      get.mockResolvedValue({ ok: true, templates: [] })

      await searchTemplates({ pricing: 'free' })

      const params = get.mock.calls[0][1].params
      expect(params.pricing).toBe('free')
    })
  })

  // =========================================================================
  // executeTemplate
  // =========================================================================

  describe('executeTemplate()', () => {
    it('calls POST /templates/:id/execute with input params', async () => {
      post.mockResolvedValue({ ok: true, executionId: 'exec-1' })

      const result = await executeTemplate('t1', { url: 'https://flyto2.com' })

      expect(post).toHaveBeenCalledWith('/templates/t1/execute', { url: 'https://flyto2.com' })
      expect(result.ok).toBe(true)
    })
  })

  // =========================================================================
  // YAML operations
  // =========================================================================

  describe('exportYAML()', () => {
    it('calls GET /templates/:id/export', async () => {
      get.mockResolvedValue({ ok: true, yaml: 'steps:\n  - module: a', filename: 'test.yaml' })

      const result = await exportYAML('t1')

      expect(get).toHaveBeenCalledWith('/templates/t1/export')
      expect(result.yaml).toContain('steps:')
      expect(result.filename).toBe('test.yaml')
    })
  })

  describe('importYAML()', () => {
    it('calls POST /templates/import/yaml with yaml_content', async () => {
      post.mockResolvedValue({ ok: true, template: { id: 't-new' } })

      const result = await importYAML('steps:\n  - module: browser.goto')

      expect(post).toHaveBeenCalledWith('/templates/import/yaml', {
        yaml_content: 'steps:\n  - module: browser.goto'
      })
      expect(result.ok).toBe(true)
    })
  })

  describe('pushYAML()', () => {
    it('calls PUT /templates/:id/push with yaml and options', async () => {
      put.mockResolvedValue({ ok: true, action: 'updated', template: { id: 't1' } })

      const result = await pushYAML('t1', 'yaml-content', { changeSummary: 'Fix bug' })

      expect(put).toHaveBeenCalledWith('/templates/t1/push', {
        yaml_content: 'yaml-content',
        change_summary: 'Fix bug',
        create_pr: undefined,
        pr_title: undefined
      })
      expect(result.action).toBe('updated')
    })

    it('supports backward-compatible string summary', async () => {
      put.mockResolvedValue({ ok: true, action: 'updated' })

      await pushYAML('t1', 'yaml', 'summary text')

      const payload = put.mock.calls[0][1]
      expect(payload.change_summary).toBe('summary text')
    })
  })

  describe('pullYAML()', () => {
    it('calls GET /templates/:id/pull', async () => {
      get.mockResolvedValue({ ok: true, yaml: 'steps:', filename: 'f.yaml' })

      const result = await pullYAML('t1')

      expect(get).toHaveBeenCalledWith('/templates/t1/pull')
      expect(result.ok).toBe(true)
      expect(result.yaml).toBe('steps:')
    })
  })

  describe('diffYAML()', () => {
    it('calls POST /templates/:id/diff with yaml_content', async () => {
      post.mockResolvedValue({ ok: true, changes: [] })

      await diffYAML('t1', 'new-yaml')

      expect(post).toHaveBeenCalledWith('/templates/t1/diff', { yaml_content: 'new-yaml' })
    })
  })

  // =========================================================================
  // unpublishTemplate
  // =========================================================================

  describe('unpublishTemplate()', () => {
    it('calls POST /templates/:id/unpublish', async () => {
      post.mockResolvedValue({ ok: true })

      const result = await unpublishTemplate('t1')

      expect(post).toHaveBeenCalledWith('/templates/t1/unpublish')
      expect(result.ok).toBe(true)
    })
  })

  // =========================================================================
  // getAvailableTags
  // =========================================================================

  describe('getAvailableTags()', () => {
    it('calls GET /templates/available-tags', async () => {
      get.mockResolvedValue({ tags: ['automation', 'browser'] })

      const tags = await getAvailableTags()

      expect(get).toHaveBeenCalledWith('/templates/available-tags')
      expect(tags).toEqual(['automation', 'browser'])
    })

    it('returns empty array on error', async () => {
      get.mockRejectedValue(new Error('fail'))

      const tags = await getAvailableTags()

      expect(tags).toEqual([])
    })
  })
})
