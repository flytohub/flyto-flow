/**
 * Integration Test: Template CRUD Flow
 *
 * Tests real template management through:
 * templateStore -> templatesAPI -> HTTP (mocked)
 *
 * Only the API module is mocked. All store logic, computed
 * properties, and state transitions are real.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

// Mock the templates API at the HTTP boundary
vi.mock('@/api/templates', () => {
  const api = {
    listTemplates: vi.fn(),
    getById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  }
  return {
    templatesAPI: {
      ...api,
      listTemplates: api.listTemplates,
      getById: api.getById,
      create: api.create,
      update: api.update,
      delete: api.delete,
    },
    default: api
  }
})

// Mock telemetry tracker (side-effect only)
vi.mock('@/utils/telemetryTracker', () => ({
  trackTemplate: { create: vi.fn(), save: vi.fn(), delete: vi.fn() }
}))

// Mock i18n
vi.mock('@/i18n', () => ({
  default: {
    global: {
      t: (key) => key
    }
  }
}))

import { useTemplateStore } from '@/stores/templateStore'
import { templatesAPI } from '@/api/templates'

// Realistic template fixtures
const TEMPLATE_1 = {
  id: 'tpl-001',
  name: 'Web Scraper',
  description: 'Scrapes web pages',
  category: 'automation',
  visibility: 'private',
  steps: [{ id: 'step-1', module: 'browser.open' }],
  createdAt: '2026-01-10T08:00:00Z',
  updatedAt: '2026-01-10T08:00:00Z'
}

const TEMPLATE_2 = {
  id: 'tpl-002',
  name: 'PDF Generator',
  description: 'Generates PDFs from HTML',
  category: 'document',
  visibility: 'public',
  steps: [{ id: 'step-1', module: 'html.render' }],
  createdAt: '2026-01-11T09:00:00Z',
  updatedAt: '2026-01-11T09:00:00Z'
}

describe('Template CRUD Flow Integration', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useTemplateStore()
    vi.clearAllMocks()
  })

  // =========================================================================
  // Fetch templates -> store updates
  // =========================================================================

  describe('fetch templates', () => {
    it('should fetch and populate templates with new response format', async () => {
      templatesAPI.listTemplates.mockResolvedValueOnce({
        ok: true,
        templates: [TEMPLATE_1, TEMPLATE_2],
        enabledCount: 2,
        totalCount: 5
      })

      expect(store.hasTemplates).toBe(false)
      expect(store.templates).toEqual([])

      await store.fetchTemplates()

      // Verify real store state updated
      expect(store.templates).toHaveLength(2)
      expect(store.hasTemplates).toBe(true)
      expect(store.templates[0].id).toBe('tpl-001')
      expect(store.templates[1].id).toBe('tpl-002')

      // Verify backend-computed counts were stored
      expect(store.enabledCount).toBe(2)
      expect(store.totalCount).toBe(5)

      // Verify loading state cleared
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('should handle legacy array response format', async () => {
      templatesAPI.listTemplates.mockResolvedValueOnce([TEMPLATE_1])

      await store.fetchTemplates()

      expect(store.templates).toHaveLength(1)
      expect(store.templates[0].name).toBe('Web Scraper')
    })

    it('should set error state on fetch failure', async () => {
      templatesAPI.listTemplates.mockRejectedValueOnce(
        new Error('Network error')
      )

      await expect(store.fetchTemplates()).rejects.toThrow('Network error')

      expect(store.error).toBe('Network error')
      expect(store.isLoading).toBe(false)
      expect(store.templates).toEqual([])
    })
  })

  // =========================================================================
  // Create template -> store updates
  // =========================================================================

  describe('create template', () => {
    it('should create template and add to store', async () => {
      const newTemplate = {
        id: 'tpl-003',
        name: 'Email Sender',
        description: 'Sends emails',
        category: 'communication'
      }

      templatesAPI.create.mockResolvedValueOnce(newTemplate)

      const result = await store.createTemplate({
        name: 'Email Sender',
        description: 'Sends emails',
        category: 'communication'
      })

      // Verify template was added to store
      expect(store.templates).toHaveLength(1)
      expect(store.templates[0].id).toBe('tpl-003')
      expect(store.hasTemplates).toBe(true)

      // Verify currentTemplate was set
      expect(store.currentTemplate).toEqual(newTemplate)

      // Verify returned data
      expect(result.id).toBe('tpl-003')
    })

    it('should maintain existing templates when adding new one', async () => {
      // Pre-populate
      store.templates = [TEMPLATE_1]

      const newTemplate = { id: 'tpl-003', name: 'New Template' }
      templatesAPI.create.mockResolvedValueOnce(newTemplate)

      await store.createTemplate({ name: 'New Template' })

      expect(store.templates).toHaveLength(2)
      expect(store.templates[0].id).toBe('tpl-001')
      expect(store.templates[1].id).toBe('tpl-003')
    })
  })

  // =========================================================================
  // Update template -> store updates
  // =========================================================================

  describe('update template', () => {
    it('should update template in-place in store', async () => {
      // Pre-populate
      store.templates = [TEMPLATE_1, TEMPLATE_2]
      store.currentTemplate = { ...TEMPLATE_1 }

      const updatedTemplate = {
        ...TEMPLATE_1,
        name: 'Advanced Web Scraper',
        updatedAt: '2026-01-15T10:00:00Z'
      }

      templatesAPI.update.mockResolvedValueOnce(updatedTemplate)

      await store.updateTemplate('tpl-001', { name: 'Advanced Web Scraper' })

      // Verify in-place update
      expect(store.templates[0].name).toBe('Advanced Web Scraper')
      expect(store.templates[1].id).toBe('tpl-002') // unchanged

      // Verify currentTemplate also updated
      expect(store.currentTemplate.name).toBe('Advanced Web Scraper')
    })

    it('should not update currentTemplate if different ID', async () => {
      store.templates = [TEMPLATE_1, TEMPLATE_2]
      store.currentTemplate = { ...TEMPLATE_2 }

      const updatedTemplate = { ...TEMPLATE_1, name: 'Updated' }
      templatesAPI.update.mockResolvedValueOnce(updatedTemplate)

      await store.updateTemplate('tpl-001', { name: 'Updated' })

      // currentTemplate should still be TEMPLATE_2
      expect(store.currentTemplate.id).toBe('tpl-002')
      expect(store.currentTemplate.name).toBe('PDF Generator')
    })
  })

  // =========================================================================
  // Delete template -> store updates
  // =========================================================================

  describe('delete template', () => {
    it('should remove template from store', async () => {
      store.templates = [TEMPLATE_1, TEMPLATE_2]
      store.currentTemplate = { ...TEMPLATE_1 }

      templatesAPI.delete.mockResolvedValueOnce({ ok: true })

      await store.deleteTemplate('tpl-001')

      expect(store.templates).toHaveLength(1)
      expect(store.templates[0].id).toBe('tpl-002')
      // Current template was the deleted one, should be cleared
      expect(store.currentTemplate).toBeNull()
    })

    it('should not clear currentTemplate if deleting different template', async () => {
      store.templates = [TEMPLATE_1, TEMPLATE_2]
      store.currentTemplate = { ...TEMPLATE_2 }

      templatesAPI.delete.mockResolvedValueOnce({ ok: true })

      await store.deleteTemplate('tpl-001')

      expect(store.templates).toHaveLength(1)
      expect(store.currentTemplate.id).toBe('tpl-002')
    })

    it('should set error on delete failure', async () => {
      store.templates = [TEMPLATE_1]

      templatesAPI.delete.mockRejectedValueOnce(
        new Error('Permission denied')
      )

      await expect(store.deleteTemplate('tpl-001')).rejects.toThrow('Permission denied')

      // Template should NOT be removed on failure
      expect(store.templates).toHaveLength(1)
      expect(store.error).toBe('Permission denied')
    })
  })

  // =========================================================================
  // Full CRUD lifecycle
  // =========================================================================

  describe('full lifecycle: fetch -> create -> update -> delete', () => {
    it('should handle complete lifecycle with real state transitions', async () => {
      // 1. Fetch initial templates
      templatesAPI.listTemplates.mockResolvedValueOnce({
        ok: true,
        templates: [TEMPLATE_1],
        enabledCount: 1,
        totalCount: 1
      })
      await store.fetchTemplates()
      expect(store.templates).toHaveLength(1)

      // 2. Create a new template
      const newTpl = { id: 'tpl-new', name: 'New Workflow' }
      templatesAPI.create.mockResolvedValueOnce(newTpl)
      await store.createTemplate({ name: 'New Workflow' })
      expect(store.templates).toHaveLength(2)

      // 3. Update the new template
      const updatedTpl = { id: 'tpl-new', name: 'Improved Workflow' }
      templatesAPI.update.mockResolvedValueOnce(updatedTpl)
      await store.updateTemplate('tpl-new', { name: 'Improved Workflow' })
      expect(store.templates.find(t => t.id === 'tpl-new').name).toBe('Improved Workflow')

      // 4. Delete the original template
      templatesAPI.delete.mockResolvedValueOnce({ ok: true })
      await store.deleteTemplate('tpl-001')
      expect(store.templates).toHaveLength(1)
      expect(store.templates[0].id).toBe('tpl-new')

      // Verify getTemplateById computed works
      expect(store.getTemplateById('tpl-new')).toBeDefined()
      expect(store.getTemplateById('tpl-001')).toBeUndefined()
    })
  })

  // =========================================================================
  // Reset
  // =========================================================================

  describe('reset', () => {
    it('should clear all state', async () => {
      store.templates = [TEMPLATE_1]
      store.currentTemplate = TEMPLATE_1
      store.enabledCount = 5
      store.totalCount = 10
      store.error = 'some error'

      store.reset()

      expect(store.templates).toEqual([])
      expect(store.currentTemplate).toBeNull()
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.enabledCount).toBe(0)
      expect(store.totalCount).toBe(0)
      expect(store.hasTemplates).toBe(false)
    })
  })
})
