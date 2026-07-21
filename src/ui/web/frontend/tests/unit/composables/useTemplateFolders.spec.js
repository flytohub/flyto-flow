import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockT, mockToast, mockStore } = vi.hoisted(() => ({
  mockT: vi.fn((key) => key),
  mockToast: { success: vi.fn(), error: vi.fn() },
  mockStore: {
    createFolder: vi.fn(),
    deleteFolder: vi.fn(),
    moveTemplates: vi.fn(),
    fetchFolders: vi.fn(),
    fetchCreated: vi.fn(),
    fetchInstalled: vi.fn()
  }
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: mockT })
}))
vi.mock('@/composables/useToast', () => ({
  useToast: () => mockToast
}))
vi.mock('@/stores/myTemplatesStore', () => ({
  useMyTemplatesStore: () => mockStore
}))

vi.mock('@/api/templates', () => ({
  templatesAPI: {
    updateFolder: vi.fn()
  }
}))

import { useTemplateFolders } from '@/composables/useTemplateFolders'

describe('useTemplateFolders', () => {
  let folders

  beforeEach(() => {
    vi.clearAllMocks()
    folders = useTemplateFolders()
  })

  it('returns the expected API', () => {
    expect(folders).toHaveProperty('showCreateFolderDialog')
    expect(folders).toHaveProperty('creatingFolder')
    expect(typeof folders.handleCreateFolder).toBe('function')
    expect(typeof folders.openRenameFolder).toBe('function')
    expect(typeof folders.handleRenameFolder).toBe('function')
    expect(typeof folders.openDeleteFolder).toBe('function')
    expect(typeof folders.handleDeleteFolder).toBe('function')
    expect(typeof folders.openMoveToFolder).toBe('function')
    expect(typeof folders.handleMoveToFolder).toBe('function')
  })

  describe('initial state', () => {
    it('all dialogs are hidden', () => {
      expect(folders.showCreateFolderDialog.value).toBe(false)
      expect(folders.showRenameFolderDialog.value).toBe(false)
      expect(folders.showDeleteFolderDialog.value).toBe(false)
      expect(folders.showMoveToFolderDialog.value).toBe(false)
    })
  })

  describe('handleCreateFolder', () => {
    it('creates folder on success', async () => {
      mockStore.createFolder.mockResolvedValue({ ok: true })
      await folders.handleCreateFolder({ name: 'New Folder', color: '#ff0000' })
      expect(mockStore.createFolder).toHaveBeenCalledWith({
        name: 'New Folder',
        color: '#ff0000',
        tab: 'created',
        parent_id: null
      })
      expect(mockToast.success).toHaveBeenCalled()
      expect(folders.showCreateFolderDialog.value).toBe(false)
    })

    it('does nothing when name is empty', async () => {
      await folders.handleCreateFolder({ name: '', color: '#000' })
      expect(mockStore.createFolder).not.toHaveBeenCalled()
    })

    it('shows error on failure', async () => {
      mockStore.createFolder.mockResolvedValue({ ok: false, error: 'Name taken' })
      await folders.handleCreateFolder({ name: 'Test', color: '#000' })
      expect(mockToast.error).toHaveBeenCalledWith('Name taken')
    })

    it('shows error on exception', async () => {
      mockStore.createFolder.mockRejectedValue(new Error('Network error'))
      await folders.handleCreateFolder({ name: 'Test', color: '#000' })
      expect(mockToast.error).toHaveBeenCalledWith('Network error')
    })

    it('resets creatingFolder flag after completion', async () => {
      mockStore.createFolder.mockResolvedValue({ ok: true })
      await folders.handleCreateFolder({ name: 'Test', color: '#000' })
      expect(folders.creatingFolder.value).toBe(false)
    })
  })

  describe('openRenameFolder', () => {
    it('sets rename target and opens dialog', () => {
      const folder = { id: 'f1', name: 'Old Name' }
      folders.openRenameFolder(folder)
      expect(folders.renameTarget.value).toEqual(folder)
      expect(folders.renameFolderName.value).toBe('Old Name')
      expect(folders.showRenameFolderDialog.value).toBe(true)
    })
  })

  describe('handleRenameFolder', () => {
    it('does nothing when no target', async () => {
      folders.renameTarget.value = null
      folders.renameFolderName.value = 'Test'
      await folders.handleRenameFolder()
      // Should not throw or call API
    })

    it('does nothing when name is empty', async () => {
      folders.renameTarget.value = { id: 'f1' }
      folders.renameFolderName.value = '   '
      await folders.handleRenameFolder()
      // API should not be called
    })
  })

  describe('openDeleteFolder', () => {
    it('sets delete target and opens dialog', () => {
      const folder = { id: 'f1' }
      folders.openDeleteFolder(folder)
      expect(folders.deleteTarget.value).toEqual(folder)
      expect(folders.showDeleteFolderDialog.value).toBe(true)
    })
  })

  describe('handleDeleteFolder', () => {
    it('deletes folder on success', async () => {
      mockStore.deleteFolder.mockResolvedValue({ ok: true })
      mockStore.fetchCreated.mockResolvedValue()
      mockStore.fetchInstalled.mockResolvedValue()
      folders.deleteTarget.value = { id: 'f1' }

      await folders.handleDeleteFolder()
      expect(mockStore.deleteFolder).toHaveBeenCalledWith('f1')
      expect(mockToast.success).toHaveBeenCalled()
      expect(folders.showDeleteFolderDialog.value).toBe(false)
      expect(folders.deleteTarget.value).toBeNull()
    })

    it('does nothing when no target', async () => {
      folders.deleteTarget.value = null
      await folders.handleDeleteFolder()
      expect(mockStore.deleteFolder).not.toHaveBeenCalled()
    })

    it('shows error on failure', async () => {
      mockStore.deleteFolder.mockResolvedValue({ ok: false, error: 'Not empty' })
      folders.deleteTarget.value = { id: 'f1' }
      await folders.handleDeleteFolder()
      expect(mockToast.error).toHaveBeenCalledWith('Not empty')
    })
  })

  describe('openMoveToFolder', () => {
    it('sets move target IDs as array', () => {
      folders.openMoveToFolder('tmpl-1')
      expect(folders.moveTargetIds.value).toEqual(['tmpl-1'])
      expect(folders.showMoveToFolderDialog.value).toBe(true)
    })

    it('accepts array of IDs', () => {
      folders.openMoveToFolder(['tmpl-1', 'tmpl-2'])
      expect(folders.moveTargetIds.value).toEqual(['tmpl-1', 'tmpl-2'])
    })
  })

  describe('handleMoveToFolder', () => {
    it('moves templates on success', async () => {
      mockStore.moveTemplates.mockResolvedValue({ ok: true })
      folders.moveTargetIds.value = ['tmpl-1', 'tmpl-2']

      await folders.handleMoveToFolder('folder-1')
      expect(mockStore.moveTemplates).toHaveBeenCalledWith(['tmpl-1', 'tmpl-2'], 'folder-1')
      expect(mockToast.success).toHaveBeenCalled()
      expect(folders.showMoveToFolderDialog.value).toBe(false)
      expect(folders.moveTargetIds.value).toEqual([])
    })

    it('shows error on failure', async () => {
      mockStore.moveTemplates.mockResolvedValue({ ok: false, error: 'Folder not found' })
      folders.moveTargetIds.value = ['tmpl-1']
      await folders.handleMoveToFolder('bad-folder')
      expect(mockToast.error).toHaveBeenCalledWith('Folder not found')
    })
  })
})
