import { describe, it, expect } from 'vitest'
import {
  deepClone,
  removeEmptyValues,
  mergeProps,
  flattenSectionsToComponents,
  componentsToSections,
  parseOptionsText,
  stringifyOptions,
  normalizeComponentId,
  generateSlug,
  transformToExportFormat,
  transformFromImportFormat,
  updateComponentProps,
  extractTemplateSummary
} from '@/utils/templateBuilder/transformers'

describe('templateBuilder transformers', () => {
  // -- Object Utils --

  describe('deepClone', () => {
    it('returns null for null', () => {
      expect(deepClone(null)).toBeNull()
    })

    it('returns primitives as-is', () => {
      expect(deepClone(42)).toBe(42)
      expect(deepClone('str')).toBe('str')
      expect(deepClone(true)).toBe(true)
      expect(deepClone(undefined)).toBe(undefined)
    })

    it('clones Date objects', () => {
      const date = new Date('2025-01-01')
      const cloned = deepClone(date)
      expect(cloned).toEqual(date)
      expect(cloned).not.toBe(date)
    })

    it('clones arrays deeply', () => {
      const arr = [1, { a: 2 }, [3]]
      const cloned = deepClone(arr)
      expect(cloned).toEqual(arr)
      expect(cloned).not.toBe(arr)
      expect(cloned[1]).not.toBe(arr[1])
    })

    it('clones objects deeply', () => {
      const obj = { a: 1, b: { c: 2 } }
      const cloned = deepClone(obj)
      expect(cloned).toEqual(obj)
      expect(cloned).not.toBe(obj)
      expect(cloned.b).not.toBe(obj.b)
    })
  })

  describe('removeEmptyValues', () => {
    it('returns input for non-object', () => {
      expect(removeEmptyValues(null)).toBeNull()
      expect(removeEmptyValues('str')).toBe('str')
    })

    it('removes null and undefined values', () => {
      expect(removeEmptyValues({ a: null, b: undefined, c: 'ok' }))
        .toEqual({ c: 'ok' })
    })

    it('removes empty strings by default', () => {
      expect(removeEmptyValues({ a: '', b: 'ok' }))
        .toEqual({ b: 'ok' })
    })

    it('keeps empty strings when removeEmptyStrings is false', () => {
      expect(removeEmptyValues({ a: '', b: 'ok' }, false))
        .toEqual({ a: '', b: 'ok' })
    })

    it('recursively cleans nested objects', () => {
      const result = removeEmptyValues({ a: { b: null, c: 'ok' } })
      expect(result).toEqual({ a: { c: 'ok' } })
    })

    it('removes nested objects that become empty', () => {
      const result = removeEmptyValues({ a: { b: null } })
      expect(result).toEqual({})
    })

    it('preserves arrays', () => {
      expect(removeEmptyValues({ a: [1, 2, 3] })).toEqual({ a: [1, 2, 3] })
    })

    it('preserves zero and false values', () => {
      expect(removeEmptyValues({ a: 0, b: false })).toEqual({ a: 0, b: false })
    })
  })

  describe('mergeProps', () => {
    it('merges defaults with custom', () => {
      const result = mergeProps({ a: 1, b: 2 }, { b: 3, c: 4 })
      expect(result).toEqual({ a: 1, b: 3, c: 4 })
    })

    it('does not mutate inputs', () => {
      const defaults = { a: 1 }
      const custom = { b: 2 }
      mergeProps(defaults, custom)
      expect(defaults).toEqual({ a: 1 })
      expect(custom).toEqual({ b: 2 })
    })
  })

  // -- Section Transformers --

  describe('flattenSectionsToComponents', () => {
    it('returns empty array for non-array', () => {
      expect(flattenSectionsToComponents(null)).toEqual([])
      expect(flattenSectionsToComponents('bad')).toEqual([])
    })

    it('returns empty array for empty sections', () => {
      expect(flattenSectionsToComponents([])).toEqual([])
    })

    it('flattens components from sections', () => {
      const sections = [{
        columnsData: [{
          components: [{ id: 'c1' }, { id: 'c2' }]
        }, {
          components: [{ id: 'c3' }]
        }]
      }]
      const result = flattenSectionsToComponents(sections)
      expect(result).toEqual([{ id: 'c1' }, { id: 'c2' }, { id: 'c3' }])
    })

    it('handles sections with no columnsData', () => {
      const sections = [{ id: 's1' }]
      expect(flattenSectionsToComponents(sections)).toEqual([])
    })

    it('handles columns with no components', () => {
      const sections = [{ columnsData: [{ other: 'data' }] }]
      expect(flattenSectionsToComponents(sections)).toEqual([])
    })
  })

  describe('componentsToSections', () => {
    it('returns empty array for null/empty', () => {
      expect(componentsToSections(null)).toEqual([])
      expect(componentsToSections([])).toEqual([])
    })

    it('wraps components in section structure', () => {
      const components = [{ id: 'c1' }, { id: 'c2' }]
      const result = componentsToSections(components)
      expect(result).toHaveLength(1)
      expect(result[0].id).toBe('section_1')
      expect(result[0].columns).toBe(1)
      expect(result[0].grid).toEqual([12])
      expect(result[0].columnsData[0].components).toEqual(components)
    })

    it('respects defaultColumns parameter', () => {
      const result = componentsToSections([{ id: 'c1' }], 2)
      expect(result[0].columns).toBe(2)
    })
  })

  // -- Option Transformers --

  describe('parseOptionsText', () => {
    it('returns empty array for falsy input', () => {
      expect(parseOptionsText(null)).toEqual([])
      expect(parseOptionsText('')).toEqual([])
      expect(parseOptionsText(undefined)).toEqual([])
    })

    it('returns empty for non-string', () => {
      expect(parseOptionsText(42)).toEqual([])
    })

    it('parses label:value format', () => {
      expect(parseOptionsText('Red:red\nBlue:blue'))
        .toEqual([{ label: 'Red', value: 'red' }, { label: 'Blue', value: 'blue' }])
    })

    it('parses plain label format (value = label)', () => {
      expect(parseOptionsText('Apple\nBanana'))
        .toEqual([{ label: 'Apple', value: 'Apple' }, { label: 'Banana', value: 'Banana' }])
    })

    it('handles colons in value', () => {
      expect(parseOptionsText('URL:http://example.com'))
        .toEqual([{ label: 'URL', value: 'http://example.com' }])
    })

    it('skips empty lines', () => {
      expect(parseOptionsText('A\n\nB'))
        .toEqual([{ label: 'A', value: 'A' }, { label: 'B', value: 'B' }])
    })

    it('trims whitespace', () => {
      expect(parseOptionsText('  Red : red  '))
        .toEqual([{ label: 'Red', value: 'red' }])
    })
  })

  describe('stringifyOptions', () => {
    it('returns empty string for non-array', () => {
      expect(stringifyOptions(null)).toBe('')
      expect(stringifyOptions('bad')).toBe('')
    })

    it('formats label:value pairs', () => {
      expect(stringifyOptions([{ label: 'Red', value: 'red' }]))
        .toBe('Red:red')
    })

    it('shows only label when label equals value', () => {
      expect(stringifyOptions([{ label: 'Apple', value: 'Apple' }]))
        .toBe('Apple')
    })

    it('skips options with no label', () => {
      expect(stringifyOptions([{ label: '', value: 'x' }, { label: 'A', value: 'a' }]))
        .toBe('A:a')
    })

    it('joins with newlines', () => {
      const result = stringifyOptions([
        { label: 'A', value: 'a' },
        { label: 'B', value: 'b' }
      ])
      expect(result).toBe('A:a\nB:b')
    })
  })

  // -- ID Utils --

  describe('normalizeComponentId', () => {
    it('returns empty string for falsy input', () => {
      expect(normalizeComponentId(null)).toBe('')
      expect(normalizeComponentId('')).toBe('')
      expect(normalizeComponentId(undefined)).toBe('')
    })

    it('returns empty for non-string', () => {
      expect(normalizeComponentId(42)).toBe('')
    })

    it('lowercases and replaces special chars', () => {
      expect(normalizeComponentId('Hello World!')).toBe('hello_world')
    })

    it('collapses multiple underscores', () => {
      expect(normalizeComponentId('a__b___c')).toBe('a_b_c')
    })

    it('strips leading/trailing underscores', () => {
      expect(normalizeComponentId('_hello_')).toBe('hello')
    })

    it('preserves hyphens', () => {
      expect(normalizeComponentId('my-component')).toBe('my-component')
    })
  })

  describe('generateSlug', () => {
    it('returns empty string for falsy input', () => {
      expect(generateSlug(null)).toBe('')
      expect(generateSlug('')).toBe('')
    })

    it('returns empty for non-string', () => {
      expect(generateSlug(42)).toBe('')
    })

    it('converts spaces to underscores', () => {
      expect(generateSlug('Hello World')).toBe('hello_world')
    })

    it('removes special characters', () => {
      expect(generateSlug('test@#$123')).toBe('test123')
    })

    it('collapses multiple underscores', () => {
      expect(generateSlug('a   b')).toBe('a_b')
    })

    it('strips leading/trailing underscores', () => {
      expect(generateSlug(' hello ')).toBe('hello')
    })
  })

  // -- Export Transformers --

  describe('transformToExportFormat', () => {
    it('wraps template data with metadata', () => {
      const data = { name: 'Test', template_id: 'test' }
      const result = transformToExportFormat(data)
      expect(result.version).toBe('1.0')
      expect(result.exported_at).toBeDefined()
      expect(result.template).toEqual(data)
      // Should be a clone, not the same reference
      expect(result.template).not.toBe(data)
    })
  })

  describe('transformFromImportFormat', () => {
    it('extracts template from new format', () => {
      const importData = {
        version: '1.0',
        exported_at: '2025-01-01',
        template: { name: 'Test' }
      }
      const result = transformFromImportFormat(importData)
      expect(result).toEqual({ name: 'Test' })
      expect(result).not.toBe(importData.template) // cloned
    })

    it('returns clone of old format (direct data)', () => {
      const data = { name: 'Test', template_id: 'test' }
      const result = transformFromImportFormat(data)
      expect(result).toEqual(data)
      expect(result).not.toBe(data)
    })
  })

  describe('updateComponentProps', () => {
    it('merges updates into component', () => {
      const component = { id: 'c1', label: 'Old' }
      const result = updateComponentProps(component, { label: 'New', extra: true })
      expect(result).toEqual({ id: 'c1', label: 'New', extra: true })
    })

    it('does not mutate original', () => {
      const component = { id: 'c1' }
      updateComponentProps(component, { label: 'New' })
      expect(component).toEqual({ id: 'c1' })
    })
  })

  describe('extractTemplateSummary', () => {
    it('extracts summary from template data', () => {
      const data = {
        template_id: 'test',
        name: 'Test Template',
        description: 'A test',
        version: '2.0',
        ui: {
          sections: [{
            columnsData: [{ components: [{ id: 'c1' }, { id: 'c2' }] }]
          }]
        },
        steps: [{ id: 'step1' }]
      }
      const summary = extractTemplateSummary(data)
      expect(summary.id).toBe('test')
      expect(summary.name).toBe('Test Template')
      expect(summary.description).toBe('A test')
      expect(summary.version).toBe('2.0')
      expect(summary.sectionsCount).toBe(1)
      expect(summary.componentsCount).toBe(2)
      expect(summary.hasWorkflow).toBe(true)
    })

    it('handles missing optional fields', () => {
      const data = { template_id: 'x', name: 'X' }
      const summary = extractTemplateSummary(data)
      expect(summary.description).toBe('')
      expect(summary.version).toBe('1.0')
      expect(summary.sectionsCount).toBe(0)
      expect(summary.componentsCount).toBe(0)
      expect(summary.hasWorkflow).toBe(false)
    })
  })
})
