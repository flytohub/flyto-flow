import { describe, it, expect, vi, beforeEach } from 'vitest'
vi.mock('js-yaml', () => ({ default: { load: vi.fn(), dump: vi.fn(d => JSON.stringify(d)) }, load: vi.fn(), dump: vi.fn(d => JSON.stringify(d)) }))
vi.mock('../composables/workflowEditor/useWorkflowImport', () => ({ importWorkflowFromYaml: vi.fn().mockResolvedValue({ success: true, nodes: [], edges: [], workflowMeta: null, checkpoints: [], warnings: [], errors: [] }) }))
vi.mock('../utils/moduleIdUtils', () => ({ isTemplateModule: vi.fn(() => false), getBaseModuleType: vi.fn(id => id) }))
import yaml from 'js-yaml'
import { detectFormat, normalizeModuleId, importTemplateData, importFromAISuggestion, importFromFile, exportToJson, exportToYaml, quickValidate } from '@/services/templateDataService'
describe('templateDataService', () => {
  beforeEach(() => vi.clearAllMocks())
  describe('detectFormat', () => {
    it('detects JSON', () => { expect(detectFormat('{"a":1}')).toBe('json') })
    it('detects YAML', () => { yaml.load.mockReturnValue({ steps: [] }); expect(detectFormat('steps:')).toBe('yaml') })
    it('returns unknown', () => { yaml.load.mockImplementation(() => { throw new Error() }); expect(detectFormat('!@#')).toBe('unknown') })
  })
  describe('normalizeModuleId', () => {
    it('returns falsy as-is', () => { expect(normalizeModuleId(null)).toBeNull() })
    it('converts underscore to dot', () => { expect(normalizeModuleId('a_b')).toBe('a.b') })
    it('keeps dotted', () => { expect(normalizeModuleId('a.b')).toBe('a.b') })
  })
  describe('importTemplateData', () => {
    it('errors on unknown', async () => { yaml.load.mockImplementation(() => { throw new Error() }); const r = await importTemplateData('!!!'); expect(r.success).toBe(false) })
    it('parses JSON', async () => { const r = await importTemplateData('{"templateId":"t1"}'); expect(r.success).toBe(true) })
  })
  describe('importFromAISuggestion', () => {
    it('errors without yaml', async () => { const r = await importFromAISuggestion({}); expect(r.success).toBe(false) })
  })
  describe('importFromFile', () => {
    it('rejects large', async () => { const r = await importFromFile({ size: 6e6, name: 'x' }); expect(r.success).toBe(false) })
    it('rejects empty', async () => { const r = await importFromFile({ size: 0, name: 'x' }); expect(r.success).toBe(false) })
  })
  describe('exportToJson', () => {
    it('pretty prints', () => { expect(exportToJson({ a: 1 })).toBe(JSON.stringify({ a: 1 }, null, 2)) })
    it('compacts', () => { expect(exportToJson({ a: 1 }, { pretty: false })).toBe('{"a":1}') })
  })
  describe('exportToYaml', () => {
    it('calls dump', () => { yaml.dump.mockReturnValue('x'); exportToYaml({ n: 1 }); expect(yaml.dump).toHaveBeenCalled() })
  })
  describe('quickValidate', () => {
    it('validates known', () => { yaml.load.mockReturnValue({ steps: [{ module: 'a' }] }); expect(quickValidate('x', vi.fn().mockReturnValue({}))).toEqual({ valid: true, issues: [] }) })
    it('reports unknown', () => { yaml.load.mockReturnValue({ steps: [{ module: 'x' }] }); expect(quickValidate('x', vi.fn().mockReturnValue(null)).valid).toBe(false) })
    it('reports empty', () => { yaml.load.mockReturnValue(null); expect(quickValidate('', vi.fn()).valid).toBe(false) })
  })
})
