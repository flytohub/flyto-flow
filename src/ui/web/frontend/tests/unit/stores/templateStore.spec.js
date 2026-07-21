import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/templates', () => ({
  templatesAPI: {
    listTemplates: vi.fn(),
    getById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  }
}))

vi.mock('@/i18n', () => ({
  default: { global: { t: (key) => key } }
}))

vi.mock('@/utils/telemetryTracker', () => ({
  trackTemplate: { create: vi.fn(), save: vi.fn(), delete: vi.fn() }
}))

import { useTemplateStore } from '@/stores/templateStore'
import { templatesAPI } from '@/api/templates'

describe('useTemplateStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useTemplateStore()
    vi.clearAllMocks()
  })

  // ==========================================================================
  // Initial State
  // ==========================================================================
  describe('initial state', () => {
    it('has correct defaults', () => {
      expect(store.templates).toEqual([])
      expect(store.currentTemplate).toBeNull()
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.hasLoaded).toBe(false)
      expect(store.isReady).toBe(false)
      expect(store.enabledCount).toBe(0)
      expect(store.totalCount).toBe(0)
    })
  })

  // ==========================================================================
  // Getters
  // ==========================================================================
  describe('getters', () => {
    it('hasTemplates returns false when empty', () => {
      expect(store.hasTemplates).toBe(false)
    })

    it('hasTemplates returns true when templates exist', () => {
      store.templates = [{ id: 't1' }]
      expect(store.hasTemplates).toBe(true)
    })

    it('getTemplateById finds template', () => {
      store.templates = [
        { id: 't1', name: 'First' },
        { id: 't2', name: 'Second' }
      ]
      expect(store.getTemplateById('t2')).toEqual({ id: 't2', name: 'Second' })
    })

    it('getTemplateById ignores invalid list entries', () => {
      store.templates = [null, 'bad', { id: 't1', name: 'First' }]
      expect(store.getTemplateById('t1')).toEqual({ id: 't1', name: 'First' })
    })

    it('getTemplateById returns undefined for missing id', () => {
      store.templates = [{ id: 't1' }]
      expect(store.getTemplateById('missing')).toBeUndefined()
    })
  })

  // ==========================================================================
  // fetchTemplates
  // ==========================================================================
  describe('fetchTemplates', () => {
    it('handles array response (old format)', async () => {
      const mockTemplates = [{ id: 't1' }, { id: 't2' }]
      templatesAPI.listTemplates.mockResolvedValue(mockTemplates)

      await store.fetchTemplates()

      expect(store.templates).toEqual(mockTemplates)
      expect(store.isLoading).toBe(false)
      expect(store.hasLoaded).toBe(true)
      expect(store.isReady).toBe(true)
    })

    it('handles object response with backend counts (new format)', async () => {
      templatesAPI.listTemplates.mockResolvedValue({
        ok: true,
        templates: [{ id: 't1' }],
        enabledCount: 5,
        totalCount: 10
      })

      await store.fetchTemplates()

      expect(store.templates).toEqual([{ id: 't1' }])
      expect(store.enabledCount).toBe(5)
      expect(store.totalCount).toBe(10)
    })

    it('normalizes partial object responses to stable empty state', async () => {
      templatesAPI.listTemplates.mockResolvedValue({
        ok: true,
        templates: [null, { id: 't1' }, 'bad'],
        enabledCount: 'bad',
        totalCount: null
      })

      await store.fetchTemplates()

      expect(store.templates).toEqual([{ id: 't1' }])
      expect(store.enabledCount).toBe(1)
      expect(store.totalCount).toBe(1)
      expect(store.error).toBeNull()
    })

    it('clears list and records error on ok false responses', async () => {
      store.templates = [{ id: 'stale' }]
      templatesAPI.listTemplates.mockResolvedValue({
        ok: false,
        error: 'backend unavailable',
        templates: null
      })

      const result = await store.fetchTemplates()

      expect(result.ok).toBe(false)
      expect(store.templates).toEqual([])
      expect(store.enabledCount).toBe(0)
      expect(store.totalCount).toBe(0)
      expect(store.error).toBe('backend unavailable')
      expect(store.hasLoaded).toBe(true)
      expect(store.isReady).toBe(false)
    })

    it('passes options to API', async () => {
      templatesAPI.listTemplates.mockResolvedValue([])

      await store.fetchTemplates({ enabled: true })

      expect(templatesAPI.listTemplates).toHaveBeenCalledWith({ enabled: true })
    })

    it('sets error on failure', async () => {
      templatesAPI.listTemplates.mockRejectedValue(new Error('Network error'))

      await expect(store.fetchTemplates()).rejects.toThrow('Network error')
      expect(store.error).toBe('Network error')
      expect(store.isLoading).toBe(false)
      expect(store.hasLoaded).toBe(false)
      expect(store.isReady).toBe(false)
    })
  })

  // ==========================================================================
  // fetchTemplateById
  // ==========================================================================
  describe('fetchTemplateById', () => {
    it('sets currentTemplate on success', async () => {
      const mockTemplate = { id: 't1', name: 'Test' }
      templatesAPI.getById.mockResolvedValue(mockTemplate)

      const result = await store.fetchTemplateById('t1')

      expect(result).toEqual(mockTemplate)
      expect(store.currentTemplate).toEqual(mockTemplate)
    })

    it('sets error on failure', async () => {
      templatesAPI.getById.mockRejectedValue(new Error('Not found'))

      await expect(store.fetchTemplateById('bad')).rejects.toThrow()
      expect(store.error).toBe('Not found')
    })
  })

  // ==========================================================================
  // createTemplate
  // ==========================================================================
  describe('createTemplate', () => {
    it('adds template to list and sets as current', async () => {
      const newTemplate = { id: 't-new', name: 'New Template' }
      templatesAPI.create.mockResolvedValue(newTemplate)

      const result = await store.createTemplate({ name: 'New Template' })

      expect(result).toEqual(newTemplate)
      expect(store.templates).toContainEqual(newTemplate)
      expect(store.currentTemplate).toEqual(newTemplate)
    })

    it('sets error on failure', async () => {
      templatesAPI.create.mockRejectedValue(new Error('Validation error'))

      await expect(store.createTemplate({})).rejects.toThrow()
      expect(store.error).toBe('Validation error')
    })
  })

  // ==========================================================================
  // updateTemplate
  // ==========================================================================
  describe('updateTemplate', () => {
    it('updates template in list', async () => {
      store.templates = [
        { id: 't1', name: 'Old Name' },
        { id: 't2', name: 'Other' }
      ]
      const updated = { id: 't1', name: 'New Name' }
      templatesAPI.update.mockResolvedValue(updated)

      await store.updateTemplate('t1', { name: 'New Name' })

      expect(store.templates[0]).toEqual(updated)
      expect(store.templates[1]).toEqual({ id: 't2', name: 'Other' })
    })

    it('updates currentTemplate if it matches', async () => {
      store.currentTemplate = { id: 't1', name: 'Old' }
      store.templates = [{ id: 't1', name: 'Old' }]
      const updated = { id: 't1', name: 'New' }
      templatesAPI.update.mockResolvedValue(updated)

      await store.updateTemplate('t1', { name: 'New' })

      expect(store.currentTemplate).toEqual(updated)
    })

    it('does not crash when template not in list', async () => {
      store.templates = []
      templatesAPI.update.mockResolvedValue({ id: 't1', name: 'Updated' })

      await store.updateTemplate('t1', { name: 'Updated' })

      expect(store.templates).toEqual([])
    })
  })

  // ==========================================================================
  // deleteTemplate
  // ==========================================================================
  describe('deleteTemplate', () => {
    it('removes template from list', async () => {
      store.templates = [{ id: 't1' }, { id: 't2' }]
      templatesAPI.delete.mockResolvedValue()

      await store.deleteTemplate('t1')

      expect(store.templates).toEqual([{ id: 't2' }])
    })

    it('clears currentTemplate if it was deleted', async () => {
      store.currentTemplate = { id: 't1' }
      store.templates = [{ id: 't1' }]
      templatesAPI.delete.mockResolvedValue()

      await store.deleteTemplate('t1')

      expect(store.currentTemplate).toBeNull()
    })

    it('does not clear currentTemplate if different one was deleted', async () => {
      store.currentTemplate = { id: 't1' }
      store.templates = [{ id: 't1' }, { id: 't2' }]
      templatesAPI.delete.mockResolvedValue()

      await store.deleteTemplate('t2')

      expect(store.currentTemplate).toEqual({ id: 't1' })
    })
  })

  // ==========================================================================
  // Utility Actions
  // ==========================================================================
  describe('setCurrentTemplate', () => {
    it('sets the current template', () => {
      store.setCurrentTemplate({ id: 't1', name: 'Test' })
      expect(store.currentTemplate).toEqual({ id: 't1', name: 'Test' })
    })
  })

  describe('clearError', () => {
    it('clears error', () => {
      store.error = 'some error'
      store.clearError()
      expect(store.error).toBeNull()
    })
  })

  describe('reset', () => {
    it('resets all state to defaults', () => {
      store.templates = [{ id: 't1' }]
      store.currentTemplate = { id: 't1' }
      store.isLoading = true
      store.error = 'err'
      store.hasLoaded = true
      store.enabledCount = 5
      store.totalCount = 10

      store.reset()

      expect(store.templates).toEqual([])
      expect(store.currentTemplate).toBeNull()
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.hasLoaded).toBe(false)
      expect(store.isReady).toBe(false)
      expect(store.enabledCount).toBe(0)
      expect(store.totalCount).toBe(0)
    })
  })
})
