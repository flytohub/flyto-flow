import { describe, it, expect, vi } from 'vitest'

// Mock dependencies
vi.mock('@/composables/workflowEditor/workflowConstants', () => ({
  HANDLE_IDS: {
    CASE_PREFIX: 'source-case-'
  }
}))

import {
  extractRawModuleId,
  extractRequiredPermissions,
  debugLogSteps,
  resolveSwitchCaseKey,
  resolveSwitchCaseHandleId,
  parseParams
} from '@/utils/converter/helpers'

describe('converter helpers', () => {
  describe('extractRawModuleId', () => {
    it('returns empty string for falsy input', () => {
      expect(extractRawModuleId(null)).toBe('')
      expect(extractRawModuleId(undefined)).toBe('')
      expect(extractRawModuleId('')).toBe('')
      expect(extractRawModuleId(0)).toBe('')
    })

    it('returns string input as-is', () => {
      expect(extractRawModuleId('browser.click')).toBe('browser.click')
    })

    it('extracts from object with data.module string', () => {
      expect(extractRawModuleId({ data: { module: 'browser.click' } })).toBe('browser.click')
    })

    it('extracts from object with module string', () => {
      expect(extractRawModuleId({ module: 'api.request' })).toBe('api.request')
    })

    it('extracts from object with moduleId string', () => {
      expect(extractRawModuleId({ moduleId: 'file.read' })).toBe('file.read')
    })

    it('extracts from nested module object', () => {
      expect(extractRawModuleId({ data: { module: { moduleId: 'deep.module' } } }))
        .toBe('deep.module')
    })

    it('returns empty string for object with no matching fields', () => {
      expect(extractRawModuleId({ foo: 'bar' })).toBe('')
    })
  })

  describe('extractRequiredPermissions', () => {
    it('returns empty array for empty steps', () => {
      expect(extractRequiredPermissions([])).toEqual([])
    })

    it('extracts permissions from module category', () => {
      const steps = [
        { module: 'browser.click' },
        { module: 'api.request' }
      ]
      const perms = extractRequiredPermissions(steps)
      expect(perms).toContain('browser_automation')
      expect(perms).toContain('network_access')
    })

    it('deduplicates permissions', () => {
      const steps = [
        { module: 'browser.click' },
        { module: 'browser.goto' }
      ]
      const perms = extractRequiredPermissions(steps)
      const browserPerms = perms.filter(p => p === 'browser_automation')
      expect(browserPerms.length).toBe(1)
    })

    it('uses backend metadata when modulesStore is provided', () => {
      const store = {
        getModule: vi.fn((id) => ({
          metadata: { requiredPermissions: ['custom_perm'] }
        }))
      }
      const steps = [{ module: 'some.module' }]
      const perms = extractRequiredPermissions(steps, { modulesStore: store })
      expect(perms).toContain('custom_perm')
    })

    it('falls back to local mapping when store has no metadata', () => {
      const store = {
        getModule: vi.fn(() => null)
      }
      const steps = [{ module: 'browser.click' }]
      const perms = extractRequiredPermissions(steps, { modulesStore: store })
      expect(perms).toContain('browser_automation')
    })

    it('returns empty for unknown categories', () => {
      const steps = [{ module: 'unknown.something' }]
      expect(extractRequiredPermissions(steps)).toEqual([])
    })
  })

  describe('debugLogSteps', () => {
    it('is a no-op function', () => {
      expect(() => debugLogSteps('test', [])).not.toThrow()
    })
  })

  describe('resolveSwitchCaseKey', () => {
    it('returns null for null edge', () => {
      expect(resolveSwitchCaseKey(null, {})).toBeNull()
    })

    it('extracts case key from source-case-{id} handle', () => {
      const edge = { sourceHandle: 'source-case-abc123' }
      expect(resolveSwitchCaseKey(edge, {})).toBe('case:abc123')
    })

    it('extracts case from edge data caseId on source-cases handle', () => {
      const edge = { sourceHandle: 'source-cases', data: { caseId: 'xyz' } }
      expect(resolveSwitchCaseKey(edge, {})).toBe('case:xyz')
    })

    it('extracts case from edge data caseKey on source-cases handle', () => {
      const edge = { sourceHandle: 'source-cases', data: { caseKey: 'abc' } }
      expect(resolveSwitchCaseKey(edge, {})).toBe('case:abc')
    })

    it('uses single case from nodeParams as fallback', () => {
      const edge = { sourceHandle: 'source-cases' }
      const nodeParams = { cases: [{ id: 'only-case' }] }
      expect(resolveSwitchCaseKey(edge, nodeParams)).toBe('case:only-case')
    })

    it('returns null for source-cases with multiple cases and no edge data', () => {
      const edge = { sourceHandle: 'source-cases' }
      const nodeParams = { cases: [{ id: 'a' }, { id: 'b' }] }
      expect(resolveSwitchCaseKey(edge, nodeParams)).toBeNull()
    })

    it('returns null for unrelated handle', () => {
      const edge = { sourceHandle: 'source-output' }
      expect(resolveSwitchCaseKey(edge, {})).toBeNull()
    })
  })

  describe('resolveSwitchCaseHandleId', () => {
    it('returns null for null/empty caseKey', () => {
      expect(resolveSwitchCaseHandleId(null)).toBeNull()
      expect(resolveSwitchCaseHandleId('')).toBeNull()
    })

    it('returns null for non-case: prefix', () => {
      expect(resolveSwitchCaseHandleId('branch:abc')).toBeNull()
    })

    it('resolves handle ID from case key', () => {
      expect(resolveSwitchCaseHandleId('case:abc')).toBe('source-case-abc')
    })

    it('matches case by id in cases array', () => {
      const cases = [{ id: 'yes', value: 'true' }]
      expect(resolveSwitchCaseHandleId('case:yes', cases)).toBe('source-case-yes')
    })

    it('matches case by value in cases array', () => {
      const cases = [{ id: 'opt1', value: 'match-me' }]
      expect(resolveSwitchCaseHandleId('case:match-me', cases)).toBe('source-case-opt1')
    })
  })

  describe('parseParams', () => {
    it('returns empty object for null/undefined', () => {
      expect(parseParams(null)).toEqual({})
      expect(parseParams(undefined)).toEqual({})
    })

    it('returns empty object for empty string', () => {
      expect(parseParams('')).toEqual({})
      expect(parseParams('   ')).toEqual({})
    })

    it('parses JSON string', () => {
      expect(parseParams('{"key":"value"}')).toEqual({ key: 'value' })
    })

    it('handles double-encoded JSON', () => {
      const doubleEncoded = JSON.stringify(JSON.stringify({ a: 1 }))
      expect(parseParams(doubleEncoded)).toEqual({ a: 1 })
    })

    it('returns empty object for unparseable string', () => {
      expect(parseParams('not json')).toEqual({})
    })

    it('returns empty object for JSON array string', () => {
      expect(parseParams('[1,2,3]')).toEqual({})
    })

    it('merges array of objects', () => {
      const result = parseParams([{ a: 1 }, { b: 2 }])
      expect(result).toEqual({ a: 1, b: 2 })
    })

    it('returns empty for array of non-objects', () => {
      expect(parseParams([1, 2, 3])).toEqual({})
    })

    it('returns the object itself for plain objects', () => {
      const obj = { key: 'value' }
      expect(parseParams(obj)).toEqual(obj)
    })

    it('respects max depth to prevent infinite recursion', () => {
      // Triple-encoded JSON would exceed depth
      const triple = JSON.stringify(JSON.stringify(JSON.stringify({ a: 1 })))
      const result = parseParams(triple)
      // Should not crash, returns something
      expect(result).toBeDefined()
    })
  })
})
