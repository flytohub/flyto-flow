import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const { mockListFolders, mockListMyTemplates } = vi.hoisted(() => ({
  mockListFolders: vi.fn(),
  mockListMyTemplates: vi.fn(),
}))

vi.mock('@/api/templates', () => ({
  templatesAPI: {
    listFolders: mockListFolders,
    listMyTemplates: mockListMyTemplates,
  },
}))

vi.mock('@/stores/userStore', () => ({
  useUserStore: () => ({
    userId: 'user-1',
    waitForAuth: vi.fn(),
  }),
}))

import { useMyTemplatesStore } from '@/stores/myTemplatesStore'

describe('myTemplatesStore folder tree', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('builds an expanded multi-level folder list from parent_id links', async () => {
    mockListFolders.mockResolvedValue({
      ok: true,
      folders: [
        { id: 'warroom', name: 'Warroom', parent_id: null, order: 0, count: 7 },
        { id: 'acme', name: 'acme', parent_id: 'warroom', order: 0, count: 7 },
        { id: 'research', name: 'Research Footprint', parent_id: 'acme', order: 0, count: 1 },
      ],
      defaultPosition: 0,
      defaultCount: 0,
      totalCount: 7,
    })

    const store = useMyTemplatesStore()
    await store.fetchFolders()

    const warroom = store.folderList.find(folder => folder.id === 'warroom')
    const project = store.folderList.find(folder => folder.id === 'acme')
    const research = store.folderList.find(folder => folder.id === 'research')

    expect(warroom).toMatchObject({ depth: 0, hasChildren: true, pathLabel: 'Warroom' })
    expect(project).toMatchObject({ depth: 1, hasChildren: true, pathLabel: 'Warroom / acme' })
    expect(research).toMatchObject({ depth: 2, hasChildren: false, pathLabel: 'Warroom / acme / Research Footprint' })
    expect(store.expandedFolders.has('warroom')).toBe(true)
    expect(store.expandedFolders.has('acme')).toBe(true)
  })

  it('builds the same multi-level tree from camelCased API folder links', async () => {
    mockListFolders.mockResolvedValue({
      ok: true,
      folders: [
        { id: 'warroom', name: 'Warroom', parentId: null, order: 0, count: 7 },
        { id: 'acme', name: 'acme', parentId: 'warroom', order: 0, count: 7 },
        { id: 'research', name: 'Research Footprint', parentId: 'acme', order: 0, count: 1 },
      ],
      defaultPosition: 0,
      defaultCount: 0,
      totalCount: 7,
    })

    const store = useMyTemplatesStore()
    await store.fetchFolders()

    expect(store.folderList.map(folder => [folder.id, folder.depth])).toEqual([
      ['__all__', 0],
      ['__default__', 0],
      ['warroom', 0],
      ['acme', 1],
      ['research', 2],
    ])
    expect(store.folderList.find(folder => folder.id === 'research').pathLabel).toBe('Warroom / acme / Research Footprint')
  })

  it('does not split a parent folder from its descendants when inserting Unfiled', async () => {
    mockListFolders.mockResolvedValue({
      ok: true,
      folders: [
        { id: 'warroom', name: 'Warroom', parent_id: null, order: 0, count: 7 },
        { id: 'acme', name: 'acme', parent_id: 'warroom', order: 0, count: 7 },
        { id: 'research', name: 'Research Footprint', parent_id: 'acme', order: 0, count: 1 },
        { id: 'other', name: 'Other', parent_id: null, order: 1, count: 0 },
      ],
      defaultPosition: 1,
      defaultCount: 0,
      totalCount: 7,
    })

    const store = useMyTemplatesStore()
    await store.fetchFolders()

    expect(store.folderList.map(folder => folder.id)).toEqual([
      '__all__',
      'warroom',
      'acme',
      'research',
      '__default__',
      'other',
    ])
  })

  it('keeps stable empty folder state for partial folder responses', async () => {
    mockListFolders.mockResolvedValue({
      ok: true,
      folders: [null, 'bad', { id: 'valid', name: null, parent_id: null, direct_count: 'bad' }],
      defaultPosition: 'bad',
      defaultCount: 'bad',
      totalCount: 3,
    })

    const store = useMyTemplatesStore()
    await store.fetchFolders()

    expect(store.folders).toEqual([
      expect.objectContaining({
        id: 'valid',
        name: '',
        directCount: 0,
      })
    ])
    expect(store.defaultFolderPosition).toBe(0)
    expect(store.defaultFolderCount).toBe(0)
    expect(store.totalCount).toBe(3)
  })

  it('clears templates and records error on non-ok template responses', async () => {
    mockListMyTemplates.mockResolvedValue({
      ok: false,
      error: 'offline',
      templates: [{ id: 'stale' }],
      total: 4,
    })

    const store = useMyTemplatesStore()
    store.templates = [{ id: 'old' }]
    await store.fetchTemplates()

    expect(store.templates).toEqual([])
    expect(store.totalFiltered).toBe(4)
    expect(store.error).toBe('offline')
  })

  it('drops invalid template entries while keeping pagination defaults', async () => {
    mockListMyTemplates.mockResolvedValue({
      ok: true,
      templates: [{ id: 'tpl-1' }, null, 'bad'],
      total: 'bad',
      hasNext: true,
      draftCount: 'bad',
      publishedCount: 2,
    })

    const store = useMyTemplatesStore()
    await store.fetchTemplates()

    expect(store.templates).toEqual([{ id: 'tpl-1' }])
    expect(store.totalFiltered).toBe(1)
    expect(store.hasNext).toBe(true)
    expect(store.stats.draftCount).toBe(0)
    expect(store.stats.publishedCount).toBe(2)
  })
})
