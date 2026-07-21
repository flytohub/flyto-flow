import { describe, it, expect, vi, beforeEach } from 'vitest'

const {
  mockToast,
  mockImportWarroomBundle,
  mockListPendingWarroomBundles,
  mockScanPendingWarroomBundles,
} = vi.hoisted(() => ({
  mockToast: { success: vi.fn(), error: vi.fn() },
  mockImportWarroomBundle: vi.fn(),
  mockListPendingWarroomBundles: vi.fn(),
  mockScanPendingWarroomBundles: vi.fn(),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => mockToast
}))

vi.mock('@/api/recipeBundles', () => ({
  importWarroomBundle: mockImportWarroomBundle,
  listPendingWarroomBundles: mockListPendingWarroomBundles,
  scanPendingWarroomBundles: mockScanPendingWarroomBundles,
}))

import { useWarroomRecipeBundleImport } from '@/composables/useWarroomRecipeBundleImport'

describe('useWarroomRecipeBundleImport', () => {
  let store

  beforeEach(() => {
    vi.clearAllMocks()
    mockListPendingWarroomBundles.mockResolvedValue({ ok: true, pending: [], rejected: [] })
    mockScanPendingWarroomBundles.mockResolvedValue({ ok: true, pending: [], rejected: [] })
    store = {
      fetchFolders: vi.fn().mockResolvedValue(),
      fetchTemplates: vi.fn().mockResolvedValue(),
      selectFolder: vi.fn(),
    }
  })

  it('runs dry-run and stores the preview result', async () => {
    mockImportWarroomBundle.mockResolvedValue({
      ok: true,
      dryRun: true,
      templateCount: 7,
      folderPaths: [['Warroom'], ['Warroom', 'acme']],
    })
    const importer = useWarroomRecipeBundleImport(store)
    importer.projectSlug.value = 'acme'
    importer.baseUrl.value = 'https://app.flyto2.com'

    const result = await importer.runDryRun()

    expect(mockImportWarroomBundle).toHaveBeenCalledWith({
      projectSlug: 'acme',
      baseUrl: 'https://app.flyto2.com',
      sourcePath: '',
      dryRun: true,
    })
    expect(result.ok).toBe(true)
    expect(importer.dryRunResult.value.templateCount).toBe(7)
    expect(importer.canImport.value).toBe(true)
  })

  it('imports after a successful dry-run and refreshes templates', async () => {
    mockImportWarroomBundle
      .mockResolvedValueOnce({ ok: true, dryRun: true, templateCount: 7 })
      .mockResolvedValueOnce({
        ok: true,
        dryRun: false,
        createdCount: 7,
        updatedCount: 0,
        folders: [
          { id: 'folder-warroom', path: ['Warroom'] },
          { id: 'folder-acme', path: ['Warroom', 'acme'] },
        ],
      })
    const importer = useWarroomRecipeBundleImport(store)
    importer.projectSlug.value = 'acme'
    importer.baseUrl.value = 'https://app.flyto2.com'

    await importer.runDryRun()
    const result = await importer.confirmImport()

    expect(result.ok).toBe(true)
    expect(mockToast.success).toHaveBeenCalledWith('Warroom recipes imported')
    expect(store.fetchFolders).toHaveBeenCalled()
    expect(store.fetchTemplates).toHaveBeenCalledWith(true)
    expect(store.selectFolder).toHaveBeenCalledWith('folder-acme')
  })

  it('sets error when dry-run fails', async () => {
    mockImportWarroomBundle.mockResolvedValue({ ok: false, error: 'bad slug' })
    const importer = useWarroomRecipeBundleImport(store)

    await importer.runDryRun()

    expect(importer.error.value).toBe('bad slug')
    expect(importer.canImport.value).toBe(false)
  })

  it('selects a pending signed bundle and approves it after dry-run', async () => {
    const pending = {
      sourcePath: '/tmp/flyto-bundle.yaml',
      bundleId: 'flyto2-warroom-smoke',
    }
    mockScanPendingWarroomBundles.mockResolvedValue({
      ok: true,
      pending: [pending],
      rejected: [],
    })
    mockImportWarroomBundle
      .mockResolvedValueOnce({ ok: true, dryRun: true, templateCount: 8 })
      .mockResolvedValueOnce({
        ok: true,
        dryRun: false,
        createdCount: 8,
        updatedCount: 0,
        folders: [{ id: 'folder-acme', path: ['Warroom', 'acme'] }],
      })
    const importer = useWarroomRecipeBundleImport(store)
    importer.projectSlug.value = 'acme'
    importer.baseUrl.value = 'https://app.flyto2.com'

    await importer.scanInbox()
    importer.selectPendingBundle(pending)
    expect(importer.sourcePath.value).toBe('/tmp/flyto-bundle.yaml')
    await importer.runDryRun()
    const result = await importer.confirmImport()

    expect(mockImportWarroomBundle).toHaveBeenCalledWith({
      projectSlug: 'acme',
      baseUrl: 'https://app.flyto2.com',
      sourcePath: '/tmp/flyto-bundle.yaml',
      dryRun: true,
    })
    expect(result.ok).toBe(true)
    expect(mockToast.success).toHaveBeenCalledWith('Warroom bundle approved')
  })
})
