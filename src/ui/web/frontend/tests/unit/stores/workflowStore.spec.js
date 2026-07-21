import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const mockWorkflowAPI = vi.hoisted(() => ({
  list: vi.fn(),
  getById: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  duplicate: vi.fn(),
  toggle: vi.fn(),
}))

vi.mock('@/api/workflows', () => ({
  workflowAPI: mockWorkflowAPI,
}))

vi.mock('@/i18n', () => ({
  default: {
    global: {
      t: (key) => key,
    },
  },
}))

import { useWorkflowStore } from '@/stores/workflowStore'

describe('workflowStore data boundaries', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('normalizes partial workflow list responses', async () => {
    mockWorkflowAPI.list.mockResolvedValue({
      ok: true,
      workflows: [{ id: 'wf-1' }, null, 'bad'],
      enabled_count: 'bad',
      total_count: 5,
    })

    const store = useWorkflowStore()
    await store.fetchWorkflows()

    expect(store.workflows).toEqual([{ id: 'wf-1' }])
    expect(store.enabledCount).toBe(1)
    expect(store.totalCount).toBe(5)
  })

  it('clears workflow list and records error on non-ok responses', async () => {
    mockWorkflowAPI.list.mockResolvedValue({
      ok: false,
      error: 'offline',
      workflows: [{ id: 'stale' }],
    })

    const store = useWorkflowStore()
    store.workflows = [{ id: 'old' }]
    await store.fetchWorkflows()

    expect(store.workflows).toEqual([])
    expect(store.error).toBe('offline')
  })

  it('does not push invalid workflow create responses', async () => {
    mockWorkflowAPI.create.mockResolvedValue(null)

    const store = useWorkflowStore()
    const result = await store.createWorkflow({ name: 'bad' })

    expect(result).toBeNull()
    expect(store.workflows).toEqual([])
    expect(store.currentWorkflow).toBeNull()
  })
})
