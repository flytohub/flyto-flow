import { describe, it, expect } from 'vitest'
import {
  asArray,
  asObject,
  normalizeListEnvelope,
  normalizeRecordingStopResponse,
  normalizeTemplateListResponse,
  normalizeTieredCatalogResponse,
  normalizeWorkflowListResponse,
  normalizeWorkflowElements
} from '@/utils/dataBoundary'

describe('dataBoundary helpers', () => {
  it('coerces non-objects and non-arrays to safe defaults', () => {
    expect(asObject(null)).toEqual({})
    expect(asObject([])).toEqual({})
    expect(asArray(null)).toEqual([])
    expect(asArray({})).toEqual([])
  })

  it('normalizes partial tiered catalog responses', () => {
    const normalized = normalizeTieredCatalogResponse({
      default: { modules: null },
      expert: null,
      modules_metadata: { 'browser.goto': { moduleId: 'browser.goto' } },
      module_categories: 'browser'
    })

    expect(normalized.defaultModules).toEqual([])
    expect(normalized.expertModules).toEqual([])
    expect(normalized.modulesMetadata).toEqual({ 'browser.goto': { moduleId: 'browser.goto' } })
    expect(normalized.moduleCategories).toEqual([])
  })

  it('normalizes template list payloads and drops invalid entries', () => {
    const normalized = normalizeTemplateListResponse({
      ok: true,
      templates: [{ id: 'tpl-1' }, null, 'bad'],
      enabled_count: 'bad',
      total_count: 4
    })

    expect(normalized.ok).toBe(true)
    expect(normalized.templates).toEqual([{ id: 'tpl-1' }])
    expect(normalized.enabledCount).toBe(1)
    expect(normalized.totalCount).toBe(4)
  })

  it('normalizes generic list envelopes without trusting bad counts', () => {
    const normalized = normalizeListEnvelope({
      ok: true,
      items: [{ id: 'one' }, null],
      total: 'bad',
      page: 'bad',
      has_next: true
    }, ['items'], { page: 2, pageSize: 10 })

    expect(normalized.items).toEqual([{ id: 'one' }])
    expect(normalized.total).toBe(1)
    expect(normalized.page).toBe(2)
    expect(normalized.pageSize).toBe(10)
    expect(normalized.hasNext).toBe(true)
  })

  it('normalizes workflow list boundaries', () => {
    const workflows = normalizeWorkflowListResponse({
      workflows: [{ id: 'wf-1' }, null],
      enabled_count: 'bad',
      total_count: 5
    })
    expect(workflows.workflows).toEqual([{ id: 'wf-1' }])
    expect(workflows.enabledCount).toBe(1)
    expect(workflows.totalCount).toBe(5)
  })

  it('normalizes recording compile responses', () => {
    const recording = normalizeRecordingStopResponse({
      ok: true,
      steps: [{ id: 'step-1' }, 'bad'],
      warnings: [{ message: 'skipped', action_index: 1 }, { code: 'empty' }],
      recording_summary: { skipped_action_count: 1 }
    })

    expect(recording.compiledSteps).toEqual([{ id: 'step-1' }])
    expect(recording.warnings).toEqual([expect.objectContaining({ message: 'skipped', action_index: 1 })])
    expect(recording.recordingSummary).toEqual({ skipped_action_count: 1 })
  })

  it('separates workflow nodes and edges from mixed payloads', () => {
    expect(normalizeWorkflowElements([
      { id: 'node-1', data: {} },
      { id: 'edge-1', source: 'node-1', target: 'node-2' },
      null,
      { bad: true }
    ])).toEqual({
      nodes: [{ id: 'node-1', data: {} }],
      edges: [{ id: 'edge-1', source: 'node-1', target: 'node-2' }]
    })
  })
})
