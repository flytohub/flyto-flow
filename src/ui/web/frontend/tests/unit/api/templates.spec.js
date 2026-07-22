import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn()
}))

import { del, get, post, put } from '@/api/client'
import { createTemplate, deleteTemplate, getTemplate, listTemplates, updateTemplate } from '@/api/templates'

describe('local workflow CRUD API', () => {
  beforeEach(() => vi.clearAllMocks())

  it('creates a local workflow without publication or identity fields', async () => {
    post.mockResolvedValue({ ok: true, template: { id: 'one', name: 'Local' } })
    const result = await createTemplate({ name: 'Local', steps: [] })
    expect(post).toHaveBeenCalledWith('/templates/', expect.objectContaining({
      name: 'Local', category: 'general', steps: []
    }))
    expect(post.mock.calls[0][1]).not.toHaveProperty('visibility')
    expect(post.mock.calls[0][1]).not.toHaveProperty('creator_id')
    expect(result.template.id).toBe('one')
  })

  it('lists only the local collection', async () => {
    get.mockResolvedValue({ ok: true, items: [{ id: 'one', name: 'Local' }], total: 1 })
    const result = await listTemplates()
    expect(get).toHaveBeenCalledWith('/templates/', { params: { page: 1, page_size: 200 } })
    expect(result.templates).toHaveLength(1)
  })

  it('loads, updates, and deletes by local identifier', async () => {
    get.mockResolvedValue({ ok: true, template: { id: 'one', name: 'Local' } })
    put.mockResolvedValue({ ok: true, template: { id: 'one', name: 'Changed' } })
    del.mockResolvedValue({ ok: true })
    await getTemplate('one')
    await updateTemplate('one', { name: 'Changed' })
    await deleteTemplate('one')
    expect(get).toHaveBeenCalledWith('/templates/one')
    expect(put).toHaveBeenCalledWith('/templates/one', expect.objectContaining({ name: 'Changed' }))
    expect(del).toHaveBeenCalledWith('/templates/one')
  })
})
