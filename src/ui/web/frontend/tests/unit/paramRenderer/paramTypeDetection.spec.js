/**
 * Parameter Type Detection Unit Tests
 *
 * Tests for detectFieldConfig, getParamComponentType, getOutputWidgetType
 */
import { describe, it, expect } from 'vitest'
import { detectFieldConfig, getParamComponentType, getOutputWidgetType } from '@/composables/paramRenderer/paramTypeDetection'

describe('detectFieldConfig', () => {
  describe('input mode (default)', () => {
    it('returns text for no schema', () => {
      expect(detectFieldConfig(null).component).toBe('text')
      expect(detectFieldConfig(undefined).component).toBe('text')
    })

    it('returns text for string type', () => {
      const result = detectFieldConfig({ type: 'string' })
      expect(result.component).toBe('text')
    })

    it('returns number for number type', () => {
      const result = detectFieldConfig({ type: 'number' })
      expect(result.component).toBe('number')
    })

    it('returns number for integer type', () => {
      const result = detectFieldConfig({ type: 'integer' })
      expect(result.component).toBe('number')
    })

    it('returns boolean for boolean type', () => {
      const result = detectFieldConfig({ type: 'boolean' })
      expect(result.component).toBe('boolean')
    })

    it('returns array for array type', () => {
      const result = detectFieldConfig({ type: 'array' })
      expect(result.component).toBe('array')
    })

    it('returns keyValue for object type without properties', () => {
      const result = detectFieldConfig({ type: 'object' })
      expect(result.component).toBe('keyValue')
    })

    it('returns fileUpload for file type', () => {
      const result = detectFieldConfig({ type: 'file' })
      expect(result.component).toBe('fileUpload')
    })

    it('returns multiselect for multiselect type', () => {
      const result = detectFieldConfig({ type: 'multiselect' })
      expect(result.component).toBe('multiselect')
    })
  })

  describe('special detectors', () => {
    it('returns select for enum fields', () => {
      const result = detectFieldConfig({ type: 'string', enum: ['a', 'b', 'c'] })
      expect(result.component).toBe('select')
    })

    it('returns select for options fields', () => {
      const result = detectFieldConfig({
        type: 'string',
        options: [{ value: 'a', label: 'A' }]
      })
      expect(result.component).toBe('select')
    })

    it('returns nestedObject for object with properties', () => {
      const result = detectFieldConfig({
        type: 'object',
        properties: { name: { type: 'string' } }
      })
      expect(result.component).toBe('nestedObject')
    })

    it('returns slider for number with min and max', () => {
      const result = detectFieldConfig({ type: 'number', min: 0, max: 100 })
      expect(result.component).toBe('slider')
    })

    it('returns imageUpload for file with image accept', () => {
      const result = detectFieldConfig({ type: 'file', accept: 'image/*' })
      expect(result.component).toBe('imageUpload')
    })
  })

  describe('format overrides', () => {
    it('returns textarea for multiline format', () => {
      const result = detectFieldConfig({ type: 'string', format: 'multiline' })
      expect(result.component).toBe('textarea')
    })

    it('returns path for path format', () => {
      const result = detectFieldConfig({ type: 'string', format: 'path' })
      expect(result.component).toBe('path')
    })

    it('returns password for password format', () => {
      const result = detectFieldConfig({ type: 'string', format: 'password' })
      expect(result.component).toBe('password')
    })

    it('returns color for color format', () => {
      const result = detectFieldConfig({ type: 'string', format: 'color' })
      expect(result.component).toBe('color')
    })

    it('returns date for date format', () => {
      const result = detectFieldConfig({ type: 'string', format: 'date' })
      expect(result.component).toBe('date')
    })

    it('returns jsonEditor for json format', () => {
      const result = detectFieldConfig({ type: 'string', format: 'json' })
      expect(result.component).toBe('jsonEditor')
    })
  })

  describe('output mode', () => {
    it('returns json-viewer for no schema', () => {
      expect(detectFieldConfig(null, 'output').component).toBe('json-viewer')
    })

    it('returns text-block for string type', () => {
      const result = detectFieldConfig({ type: 'string' }, 'output')
      expect(result.widget).toBe('text-block')
    })

    it('returns number-display for number type', () => {
      const result = detectFieldConfig({ type: 'number' }, 'output')
      expect(result.widget).toBe('number-display')
    })

    it('returns status-badge for boolean type', () => {
      const result = detectFieldConfig({ type: 'boolean' }, 'output')
      expect(result.widget).toBe('status-badge')
    })

    it('returns table-view for array type', () => {
      const result = detectFieldConfig({ type: 'array' }, 'output')
      expect(result.widget).toBe('table-view')
    })

    it('returns image-preview for image format output', () => {
      const result = detectFieldConfig({ type: 'string', format: 'image' }, 'output')
      expect(result.widget).toBe('image-preview')
    })
  })
})

describe('getParamComponentType', () => {
  it('delegates to detectFieldConfig input mode', () => {
    expect(getParamComponentType({ type: 'string' })).toBe('text')
    expect(getParamComponentType({ type: 'boolean' })).toBe('boolean')
    expect(getParamComponentType({ type: 'string', enum: ['a'] })).toBe('select')
  })
})

describe('getOutputWidgetType', () => {
  it('delegates to detectFieldConfig output mode', () => {
    expect(getOutputWidgetType({ type: 'string' })).toBe('text-block')
    expect(getOutputWidgetType({ type: 'number' })).toBe('number-display')
  })

  it('auto-detects from string value when no schema', () => {
    expect(getOutputWidgetType(null, 'hello')).toBe('text-block')
    expect(getOutputWidgetType(null, 'https://example.com')).toBe('link-button')
    expect(getOutputWidgetType(null, 'data:image/png;base64,abc')).toBe('image-preview')
  })

  it('auto-detects from number value when no schema', () => {
    expect(getOutputWidgetType(null, 42)).toBe('number-display')
  })

  it('auto-detects from boolean value when no schema', () => {
    expect(getOutputWidgetType(null, true)).toBe('status-badge')
  })

  it('auto-detects from array value when no schema', () => {
    expect(getOutputWidgetType(null, [1, 2, 3])).toBe('table-view')
  })

  it('auto-detects from object value when no schema', () => {
    expect(getOutputWidgetType(null, { key: 'val' })).toBe('json-viewer')
  })
})
