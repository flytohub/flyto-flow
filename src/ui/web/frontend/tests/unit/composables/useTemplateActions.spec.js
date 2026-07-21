import { describe, it, expect, vi, beforeEach } from 'vitest'

const {
  mockPush, mockT, mockToast, mockTemplatesAPI, mockClearCache
} = vi.hoisted(() => ({
  mockPush: vi.fn(),
  mockT: vi.fn((key) => key),
  mockToast: { success: vi.fn(), error: vi.fn() },
  mockTemplatesAPI: {
    addToLibrary: vi.fn(),
    deleteTemplate: vi.fn(),
    removeFromLibrary: vi.fn(),
    forkTemplate: vi.fn(),
    syncPurchase: vi.fn(),
    updateLibrarySettings: vi.fn()
  },
  mockClearCache: vi.fn()
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush })
}))
vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: mockT })
}))
vi.mock('@/composables/useToast', () => ({
  useToast: () => mockToast
}))
vi.mock('@/api/templates', () => ({
  templatesAPI: mockTemplatesAPI
}))
vi.mock('@/stores/modulesStore', () => ({
  useModulesStore: () => ({ clearCache: mockClearCache })
}))

import { useTemplateActions } from '@/composables/useTemplateActions'

describe('useTemplateActions', () => {
  let actions
  let mockStore

  beforeEach(() => {
    vi.clearAllMocks()
    mockStore = { loadAll: vi.fn() }
    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) }
    })
    actions = useTemplateActions(mockStore)
  })

  it('returns expected API', () => {
    expect(actions).toHaveProperty('showCreateModal')
    expect(actions).toHaveProperty('showDeleteDialog')
    expect(typeof actions.createTemplate).toBe('function')
    expect(typeof actions.openTemplate).toBe('function')
    expect(typeof actions.editTemplate).toBe('function')
    expect(typeof actions.deleteTemplate).toBe('function')
    expect(typeof actions.confirmDelete).toBe('function')
    expect(typeof actions.duplicateTemplate).toBe('function')
    expect(typeof actions.shareTemplate).toBe('function')
    expect(typeof actions.forkTemplate).toBe('function')
    expect(typeof actions.syncTemplate).toBe('function')
    expect(typeof actions.toggleMenu).toBe('function')
    expect(typeof actions.goToMarketplace).toBe('function')
  })

  describe('initial state', () => {
    it('all modals are hidden', () => {
      expect(actions.showCreateModal.value).toBe(false)
      expect(actions.showEditModal.value).toBe(false)
      expect(actions.showDeleteDialog.value).toBe(false)
      expect(actions.duplicating.value).toBe(false)
      expect(actions.deleting.value).toBe(false)
    })
  })

  describe('createTemplate', () => {
    it('opens create modal', () => {
      actions.createTemplate()
      expect(actions.showCreateModal.value).toBe(true)
    })
  })

  describe('onTemplateCreated', () => {
    it('navigates to builder', () => {
      actions.onTemplateCreated('tmpl-123')
      expect(mockPush).toHaveBeenCalledWith('/templates/builder/tmpl-123')
    })
  })

  describe('openTemplate', () => {
    it('navigates using templateId', () => {
      actions.openTemplate({ templateId: 'tmpl-1' })
      expect(mockPush).toHaveBeenCalledWith('/templates/builder/tmpl-1')
    })

    it('falls back to id', () => {
      actions.openTemplate({ id: 'tmpl-2' })
      expect(mockPush).toHaveBeenCalledWith('/templates/builder/tmpl-2')
    })
  })

  describe('editTemplate', () => {
    it('opens edit modal and sets target', () => {
      const item = { id: 'tmpl-1', name: 'Test' }
      actions.editTemplate(item)
      expect(actions.showEditModal.value).toBe(true)
      expect(actions.editTarget.value).toEqual(item)
      expect(actions.openMenuId.value).toBeNull()
    })
  })

  describe('runTemplate', () => {
    it('navigates with preview mode', () => {
      actions.runTemplate({ templateId: 'tmpl-1' })
      expect(mockPush).toHaveBeenCalledWith('/templates/builder/tmpl-1?mode=preview')
    })
  })

  describe('shareTemplate', () => {
    it('copies URL to clipboard and shows success toast', async () => {
      await actions.shareTemplate({ templateId: 'tmpl-1' })
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        expect.stringContaining('/templates/tmpl-1')
      )
      expect(mockToast.success).toHaveBeenCalled()
    })
  })

  describe('duplicateTemplate', () => {
    it('calls addToLibrary and reloads', async () => {
      mockTemplatesAPI.addToLibrary.mockResolvedValue({ ok: true })
      await actions.duplicateTemplate({ templateId: 'tmpl-1' })
      expect(mockTemplatesAPI.addToLibrary).toHaveBeenCalledWith('tmpl-1')
      expect(mockStore.loadAll).toHaveBeenCalled()
      expect(mockClearCache).toHaveBeenCalled()
      expect(mockToast.success).toHaveBeenCalled()
    })

    it('shows error on failure', async () => {
      mockTemplatesAPI.addToLibrary.mockRejectedValue(new Error('fail'))
      await actions.duplicateTemplate({ id: 'tmpl-1' })
      expect(mockToast.error).toHaveBeenCalled()
    })

    it('prevents double-click (duplicating guard)', async () => {
      mockTemplatesAPI.addToLibrary.mockResolvedValue({ ok: true })
      actions.duplicating.value = true
      await actions.duplicateTemplate({ id: 'tmpl-1' })
      expect(mockTemplatesAPI.addToLibrary).not.toHaveBeenCalled()
    })
  })

  describe('deleteTemplate + confirmDelete', () => {
    it('opens delete dialog', () => {
      const item = { id: 'tmpl-1' }
      actions.deleteTemplate(item)
      expect(actions.showDeleteDialog.value).toBe(true)
      expect(actions.deleteTarget.value).toEqual(item)
    })

    it('confirms delete for owned template', async () => {
      mockTemplatesAPI.deleteTemplate.mockResolvedValue({ ok: true })
      actions.deleteTarget.value = { id: 'tmpl-1' }
      actions.showDeleteDialog.value = true

      await actions.confirmDelete()
      expect(mockTemplatesAPI.deleteTemplate).toHaveBeenCalledWith('tmpl-1')
      expect(mockStore.loadAll).toHaveBeenCalled()
      expect(mockToast.success).toHaveBeenCalled()
      expect(actions.showDeleteDialog.value).toBe(false)
    })

    it('confirms delete for installed template', async () => {
      mockTemplatesAPI.removeFromLibrary.mockResolvedValue({ ok: true })
      actions.deleteTarget.value = { templateId: 'tmpl-1', _source: 'installed' }
      actions.showDeleteDialog.value = true

      await actions.confirmDelete()
      expect(mockTemplatesAPI.removeFromLibrary).toHaveBeenCalledWith('tmpl-1')
    })

    it('shows error on delete failure', async () => {
      mockTemplatesAPI.deleteTemplate.mockResolvedValue({ ok: false, error: 'Not found' })
      actions.deleteTarget.value = { id: 'tmpl-1' }

      await actions.confirmDelete()
      expect(mockToast.error).toHaveBeenCalledWith('Not found')
    })

    it('does nothing when deleteTarget is null', async () => {
      actions.deleteTarget.value = null
      await actions.confirmDelete()
      expect(mockTemplatesAPI.deleteTemplate).not.toHaveBeenCalled()
    })
  })

  describe('cancelDelete', () => {
    it('closes delete dialog and clears target', () => {
      actions.deleteTarget.value = { id: 'tmpl-1' }
      actions.showDeleteDialog.value = true
      actions.cancelDelete()
      expect(actions.showDeleteDialog.value).toBe(false)
      expect(actions.deleteTarget.value).toBeNull()
    })
  })

  describe('publishTemplate', () => {
    it('navigates to publish page', () => {
      actions.publishTemplate({ templateId: 'tmpl-1' })
      expect(mockPush).toHaveBeenCalledWith('/templates/tmpl-1/publish')
    })
  })

  describe('forkTemplate', () => {
    it('forks and reloads on success', async () => {
      mockTemplatesAPI.forkTemplate.mockResolvedValue({ ok: true })
      await actions.forkTemplate({ templateId: 'tmpl-1', purchaseId: 'p1' })
      expect(mockTemplatesAPI.forkTemplate).toHaveBeenCalledWith('tmpl-1', 'p1')
      expect(mockStore.loadAll).toHaveBeenCalled()
      expect(mockToast.success).toHaveBeenCalled()
    })

    it('shows error on fork failure', async () => {
      mockTemplatesAPI.forkTemplate.mockResolvedValue({ ok: false, error: 'Forbidden' })
      await actions.forkTemplate({ id: 'tmpl-1' })
      expect(mockToast.error).toHaveBeenCalledWith('Forbidden')
    })
  })

  describe('syncTemplate', () => {
    it('syncs and reloads on success', async () => {
      mockTemplatesAPI.syncPurchase.mockResolvedValue({ ok: true })
      await actions.syncTemplate({ purchaseId: 'p1' })
      expect(mockTemplatesAPI.syncPurchase).toHaveBeenCalledWith('p1')
      expect(mockStore.loadAll).toHaveBeenCalled()
    })

    it('shows error when no purchaseId', async () => {
      await actions.syncTemplate({})
      expect(mockToast.error).toHaveBeenCalled()
    })
  })

  describe('handleUpdateAutoUpdate', () => {
    it('updates auto-update setting', async () => {
      mockTemplatesAPI.updateLibrarySettings.mockResolvedValue({ ok: true })
      const item = { purchaseId: 'p1', purchaseContext: { autoUpdate: false } }
      await actions.handleUpdateAutoUpdate(item, true)
      expect(mockTemplatesAPI.updateLibrarySettings).toHaveBeenCalledWith('p1', { autoUpdate: true })
      expect(item.purchaseContext.autoUpdate).toBe(true)
    })

    it('shows error when no purchaseId', async () => {
      await actions.handleUpdateAutoUpdate({}, true)
      expect(mockToast.error).toHaveBeenCalled()
    })
  })

  describe('toggleMenu', () => {
    it('opens menu by id', () => {
      actions.toggleMenu('tmpl-1')
      expect(actions.openMenuId.value).toBe('tmpl-1')
    })

    it('closes menu when same id toggled', () => {
      actions.toggleMenu('tmpl-1')
      actions.toggleMenu('tmpl-1')
      expect(actions.openMenuId.value).toBeNull()
    })
  })

  describe('goToMarketplace', () => {
    it('navigates to marketplace', () => {
      actions.goToMarketplace()
      expect(mockPush).toHaveBeenCalledWith('/marketplace')
    })
  })
})
