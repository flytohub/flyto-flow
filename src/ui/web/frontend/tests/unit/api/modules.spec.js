import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/client', () => ({
  get: vi.fn()
}))

import { get } from '@/api/client'
import {
  getModule,
  getTieredCatalog,
  validateConnection,
  validateInsertion,
  getStarterModules,
  getConnectableForReplacement,
  getConnectableModules
} from '@/api/modules'

describe('Modules API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // =========================================================================
  // getModule
  // =========================================================================

  describe('getModule()', () => {
    it('calls GET /modules/:id with default lang=en', async () => {
      get.mockResolvedValue({ moduleId: 'browser.goto', name: 'Go To URL' })

      const result = await getModule('browser.goto')

      expect(get).toHaveBeenCalledWith('/modules/browser.goto?lang=en')
      expect(result.moduleId).toBe('browser.goto')
    })

    it('passes custom lang parameter', async () => {
      get.mockResolvedValue({ moduleId: 'browser.goto' })

      await getModule('browser.goto', 'zh-TW')

      expect(get).toHaveBeenCalledWith('/modules/browser.goto?lang=zh-TW')
    })
  })

  // =========================================================================
  // getTieredCatalog
  // =========================================================================

  describe('getTieredCatalog()', () => {
    it('calls GET /modules/tiered with default params', async () => {
      get.mockResolvedValue({ ok: true, categories: [] })

      await getTieredCatalog()

      const callUrl = get.mock.calls[0][0]
      expect(callUrl).toContain('/modules/tiered?')
      expect(callUrl).toContain('lang=en')
      expect(callUrl).toContain('include_expert=true')
      expect(callUrl).toContain('include_templates=true')
      expect(callUrl).toContain('skip_access_control=true')
    })

    it('appends excludeTemplateId when provided', async () => {
      get.mockResolvedValue({ ok: true })

      await getTieredCatalog({ excludeTemplateId: 'tmpl-123' })

      const callUrl = get.mock.calls[0][0]
      expect(callUrl).toContain('exclude_template_id=tmpl-123')
    })

    it('respects custom lang and includeExpert=false', async () => {
      get.mockResolvedValue({ ok: true })

      await getTieredCatalog({ lang: 'ja', includeExpert: false })

      const callUrl = get.mock.calls[0][0]
      expect(callUrl).toContain('lang=ja')
      expect(callUrl).toContain('include_expert=false')
    })
  })

  // =========================================================================
  // validateConnection
  // =========================================================================

  describe('validateConnection()', () => {
    it('calls GET /modules/validate-connection with source and target', async () => {
      get.mockResolvedValue({ valid: true })

      await validateConnection('browser.goto', 'browser.click')

      const callUrl = get.mock.calls[0][0]
      expect(callUrl).toContain('/modules/validate-connection?')
      expect(callUrl).toContain('source=browser.goto')
      expect(callUrl).toContain('target=browser.click')
    })

    it('includes sourcePort and targetPort when provided', async () => {
      get.mockResolvedValue({ valid: true })

      await validateConnection('a', 'b', [], 'output_1', 'input_2')

      const callUrl = get.mock.calls[0][0]
      expect(callUrl).toContain('source_port=output_1')
      expect(callUrl).toContain('target_port=input_2')
    })

    it('includes context when provided', async () => {
      get.mockResolvedValue({ valid: true })

      await validateConnection('a', 'b', ['c', 'd'])

      const callUrl = get.mock.calls[0][0]
      expect(callUrl).toContain('context=c%2Cd')
    })
  })

  // =========================================================================
  // validateInsertion
  // =========================================================================

  describe('validateInsertion()', () => {
    it('calls GET /modules/validate-insertion with correct params', async () => {
      get.mockResolvedValue({ valid: true })

      await validateInsertion('a', 'b', 'c')

      const callUrl = get.mock.calls[0][0]
      expect(callUrl).toContain('/modules/validate-insertion?')
      expect(callUrl).toContain('source=a')
      expect(callUrl).toContain('target=b')
      expect(callUrl).toContain('downstream=c')
      expect(callUrl).toContain('source_port=output')
      expect(callUrl).toContain('target_port=input')
    })
  })

  // =========================================================================
  // getStarterModules
  // =========================================================================

  describe('getStarterModules()', () => {
    it('calls GET /modules/starters and normalizes module IDs', async () => {
      get.mockResolvedValue({
        modules: [
          { module_id: 'browser.goto', name: 'Go To', start_requires_params: ['url'] },
          { moduleId: 'data.csv', name: 'CSV', startRequiresParams: [] }
        ]
      })

      const result = await getStarterModules()

      expect(get).toHaveBeenCalledWith(expect.stringContaining('/modules/starters'))
      expect(result.modules[0].moduleId).toBe('browser.goto')
      expect(result.modules[0].startRequiresParams).toEqual(['url'])
      expect(result.modules[1].moduleId).toBe('data.csv')
    })

    it('passes includeComposites param', async () => {
      get.mockResolvedValue({ modules: [] })

      await getStarterModules(false)

      expect(get).toHaveBeenCalledWith(expect.stringContaining('includeComposites=false'))
    })
  })

  // =========================================================================
  // getConnectableForReplacement
  // =========================================================================

  describe('getConnectableForReplacement()', () => {
    it('calls GET /modules/connectable-for-replacement with default limit', async () => {
      get.mockResolvedValue({ modules: [] })

      await getConnectableForReplacement()

      const callUrl = get.mock.calls[0][0]
      expect(callUrl).toContain('/modules/connectable-for-replacement?')
      expect(callUrl).toContain('limit=200')
    })

    it('includes upstream and downstream module params', async () => {
      get.mockResolvedValue({ modules: [] })

      await getConnectableForReplacement({
        upstreamModule: 'browser.goto',
        downstreamModule: 'browser.click'
      })

      const callUrl = get.mock.calls[0][0]
      expect(callUrl).toContain('upstream_module=browser.goto')
      expect(callUrl).toContain('downstream_module=browser.click')
    })
  })

  // =========================================================================
  // getConnectableModules
  // =========================================================================

  describe('getConnectableModules()', () => {
    it('calls GET /modules/connectable with moduleId and direction', async () => {
      get.mockResolvedValue({ modules: [] })

      await getConnectableModules('browser.goto', { direction: 'next' })

      const callUrl = get.mock.calls[0][0]
      expect(callUrl).toContain('/modules/connectable?')
      expect(callUrl).toContain('module_id=browser.goto')
      expect(callUrl).toContain('direction=next')
    })

    it('includes search and category when provided', async () => {
      get.mockResolvedValue({ modules: [] })

      await getConnectableModules('browser.goto', {
        direction: 'prev',
        search: 'click',
        category: 'browser'
      })

      const callUrl = get.mock.calls[0][0]
      expect(callUrl).toContain('direction=prev')
      expect(callUrl).toContain('search=click')
      expect(callUrl).toContain('category=browser')
    })
  })
})
