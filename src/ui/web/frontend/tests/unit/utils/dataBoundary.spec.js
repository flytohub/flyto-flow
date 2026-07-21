import { describe, it, expect } from 'vitest'
import {
  asArray,
  asObject,
  normalizeCreatorProfile,
  normalizeCreatorTemplatesResponse,
  normalizeFoldersResponse,
  normalizeListEnvelope,
  normalizeMyTemplatesResponse,
  normalizePeopleListResponse,
  normalizeRecipeBundlesResponse,
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

  it('normalizes workflow and my-template list boundaries', () => {
    const workflows = normalizeWorkflowListResponse({
      workflows: [{ id: 'wf-1' }, null],
      enabled_count: 'bad',
      total_count: 5
    })
    const templates = normalizeMyTemplatesResponse({
      ok: false,
      error: 'nope',
      templates: 'bad',
      draft_count: 'bad',
      published_count: 2
    })

    expect(workflows.workflows).toEqual([{ id: 'wf-1' }])
    expect(workflows.enabledCount).toBe(1)
    expect(workflows.totalCount).toBe(5)
    expect(templates.ok).toBe(false)
    expect(templates.templates).toEqual([])
    expect(templates.error).toBe('nope')
    expect(templates.publishedCount).toBe(2)
  })

  it('normalizes folders and recording compile responses', () => {
    const folders = normalizeFoldersResponse({
      folders: [{ id: 'folder-1', parent_id: 'root', direct_count: 'bad', path: 'bad' }, null],
      default_position: 'bad',
      total_count: 4
    })
    const recording = normalizeRecordingStopResponse({
      ok: true,
      steps: [{ id: 'step-1' }, 'bad'],
      warnings: [{ message: 'skipped', action_index: 1 }, { code: 'empty' }],
      recording_summary: { skipped_action_count: 1 }
    })

    expect(folders.folders).toEqual([expect.objectContaining({
      id: 'folder-1',
      parentId: 'root',
      directCount: 0,
      path: []
    })])
    expect(folders.totalCount).toBe(4)
    expect(recording.compiledSteps).toEqual([{ id: 'step-1' }])
    expect(recording.warnings).toEqual([expect.objectContaining({ message: 'skipped', action_index: 1 })])
    expect(recording.recordingSummary).toEqual({ skipped_action_count: 1 })
  })

  it('normalizes creator and bundle response boundaries', () => {
    expect(normalizeCreatorProfile({
      id: 123,
      display_name: 'Ada',
      followers_count: 'bad',
      is_creator: true
    })).toEqual(expect.objectContaining({
      id: '',
      displayName: 'Ada',
      followersCount: 0,
      isCreator: true
    }))

    expect(normalizeCreatorTemplatesResponse({ items: [{ id: 'tpl' }, null] }).templates).toEqual([{ id: 'tpl' }])
    expect(normalizePeopleListResponse({ followers: [{ id: 'u1' }, 'bad'] }, 'followers').followers).toEqual([
      expect.objectContaining({ id: 'u1' })
    ])
    expect(normalizeRecipeBundlesResponse({ ok: false, bundles: 'bad', error: 'offline' })).toEqual(expect.objectContaining({
      ok: false,
      bundles: [],
      error: 'offline'
    }))
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
