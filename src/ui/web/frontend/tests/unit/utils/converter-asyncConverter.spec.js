import { describe, it, expect, vi } from 'vitest'

// Mock dependencies
vi.mock('@/api/workflows', () => ({
  workflowAPI: {
    vueFlowToSteps: vi.fn(),
    stepsToVueFlow: vi.fn()
  }
}))

vi.mock('@/composables/workflowEditor/workflowConstants', () => ({
  separateElements: vi.fn((elements) => {
    const nodes = elements.filter(e => !e.source)
    const edges = elements.filter(e => e.source)
    return { nodes, edges }
  }),
  applyEdgeVisuals: vi.fn((edge) => ({ ...edge, styled: true })),
  HANDLE_IDS: { CASE_PREFIX: 'source-case-' }
}))

vi.mock('@/utils/converter/helpers', () => ({
  extractRawModuleId: vi.fn((v) => {
    if (typeof v === 'string') return v
    return ''
  })
}))

import {
  elementsToBackendStepsAsync,
  backendStepsToElementsAsync,
  ConversionError,
  ConversionErrorCodes
} from '@/utils/converter/asyncConverter'
import { workflowAPI } from '@/api/workflows'

describe('asyncConverter', () => {
  describe('ConversionError', () => {
    it('creates error with code and details', () => {
      const err = new ConversionError('test msg', 'TEST_CODE', { extra: 'data' })
      expect(err.message).toBe('test msg')
      expect(err.code).toBe('TEST_CODE')
      expect(err.details).toEqual({ extra: 'data' })
      expect(err.name).toBe('ConversionError')
    })
  })

  describe('ConversionErrorCodes', () => {
    it('has expected codes', () => {
      expect(ConversionErrorCodes.BACKEND_UNAVAILABLE).toBe('BACKEND_UNAVAILABLE')
      expect(ConversionErrorCodes.CONVERSION_FAILED).toBe('CONVERSION_FAILED')
      expect(ConversionErrorCodes.INVALID_RESPONSE).toBe('INVALID_RESPONSE')
    })
  })

  describe('elementsToBackendStepsAsync', () => {
    it('returns empty array for no nodes', async () => {
      const result = await elementsToBackendStepsAsync([])
      expect(result).toEqual([])
    })

    it('calls backend API and returns steps', async () => {
      workflowAPI.vueFlowToSteps.mockResolvedValue({
        ok: true,
        steps: [{ id: 'step1', module: 'browser.click' }]
      })

      const elements = [
        { id: 'n1', type: 'custom', position: { x: 0, y: 0 }, data: { module: 'browser.click' } }
      ]
      const result = await elementsToBackendStepsAsync(elements)
      expect(result).toEqual([{ id: 'step1', module: 'browser.click' }])
    })

    it('throws ConversionError when API returns not ok', async () => {
      workflowAPI.vueFlowToSteps.mockResolvedValue({
        ok: false,
        error: 'conversion error'
      })

      const elements = [{ id: 'n1', type: 'custom', position: { x: 0, y: 0 }, data: {} }]
      await expect(elementsToBackendStepsAsync(elements)).rejects.toThrow(ConversionError)
    })

    it('throws BACKEND_UNAVAILABLE on network error', async () => {
      workflowAPI.vueFlowToSteps.mockRejectedValue(new Error('Network error'))

      const elements = [{ id: 'n1', type: 'custom', position: { x: 0, y: 0 }, data: {} }]
      try {
        await elementsToBackendStepsAsync(elements)
        expect.unreachable()
      } catch (err) {
        expect(err).toBeInstanceOf(ConversionError)
        expect(err.code).toBe(ConversionErrorCodes.BACKEND_UNAVAILABLE)
      }
    })
  })

  describe('backendStepsToElementsAsync', () => {
    it('returns empty arrays for null/empty steps', async () => {
      expect(await backendStepsToElementsAsync(null)).toEqual({ nodes: [], edges: [] })
      expect(await backendStepsToElementsAsync([])).toEqual({ nodes: [], edges: [] })
      expect(await backendStepsToElementsAsync('not array')).toEqual({ nodes: [], edges: [] })
    })

    it('calls backend API and returns nodes/edges', async () => {
      workflowAPI.stepsToVueFlow.mockResolvedValue({
        ok: true,
        nodes: [{ id: 'n1', data: { module: 'browser.click' } }],
        edges: [{ id: 'e1', source: 'n1', target: 'n2' }]
      })

      const result = await backendStepsToElementsAsync([{ id: 'step1' }])
      expect(result.nodes.length).toBe(1)
      expect(result.edges.length).toBe(1)
      expect(result.edges[0].styled).toBe(true) // applyEdgeVisuals applied
    })

    it('applies icon from getModuleById', async () => {
      workflowAPI.stepsToVueFlow.mockResolvedValue({
        ok: true,
        nodes: [{ id: 'n1', data: { module: 'browser.click' } }],
        edges: []
      })

      const mockIconMap = { Globe: 'GlobeComponent' }
      const getModuleById = vi.fn(() => ({ icon: 'Globe', color: '#ff0000' }))

      const result = await backendStepsToElementsAsync(
        [{ id: 'step1' }],
        { getModuleById, iconMap: mockIconMap }
      )
      expect(result.nodes[0].data.icon).toBe('GlobeComponent')
      expect(result.nodes[0].data.color).toBe('#ff0000')
    })

    it('throws ConversionError when API returns not ok', async () => {
      workflowAPI.stepsToVueFlow.mockResolvedValue({ ok: false, error: 'fail' })

      await expect(
        backendStepsToElementsAsync([{ id: 'step1' }])
      ).rejects.toThrow(ConversionError)
    })

    it('throws BACKEND_UNAVAILABLE on network error', async () => {
      workflowAPI.stepsToVueFlow.mockRejectedValue(new Error('timeout'))

      try {
        await backendStepsToElementsAsync([{ id: 'step1' }])
        expect.unreachable()
      } catch (err) {
        expect(err).toBeInstanceOf(ConversionError)
        expect(err.code).toBe(ConversionErrorCodes.BACKEND_UNAVAILABLE)
      }
    })
  })
})
