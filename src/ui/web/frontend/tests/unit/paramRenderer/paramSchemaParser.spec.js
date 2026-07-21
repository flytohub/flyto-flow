/**
 * Parameter Schema Parser Unit Tests
 *
 * Tests for parseParamsSchema, parseOutputSchema, normalizeSchema
 */
import { describe, it, expect } from 'vitest'
import { parseParamsSchema, parseOutputSchema } from '@/composables/paramRenderer/paramSchemaParser'

describe('parseParamsSchema', () => {
  it('returns empty array for null/undefined schema', () => {
    expect(parseParamsSchema(null)).toEqual([])
    expect(parseParamsSchema(undefined)).toEqual([])
  })

  it('parses JSON Schema format (type: object with properties)', () => {
    const schema = {
      type: 'object',
      properties: {
        name: { type: 'string', label: 'Name', description: 'User name' },
        age: { type: 'number', label: 'Age', minimum: 0 }
      },
      required: ['name']
    }

    const fields = parseParamsSchema(schema)
    expect(fields).toHaveLength(2)

    expect(fields[0].key).toBe('name')
    expect(fields[0].label).toBe('Name')
    expect(fields[0].description).toBe('User name')
    expect(fields[0].type).toBe('string')
    expect(fields[0].required).toBe(true)

    expect(fields[1].key).toBe('age')
    expect(fields[1].label).toBe('Age')
    expect(fields[1].type).toBe('number')
    expect(fields[1].min).toBe(0)
  })

  it('parses flat properties dict (no type/properties wrapper)', () => {
    const schema = {
      url: { type: 'string', label: 'URL', format: 'url' },
      timeout: { type: 'number', label: 'Timeout', default: 30 }
    }

    const fields = parseParamsSchema(schema)
    expect(fields).toHaveLength(2)
    expect(fields[0].key).toBe('url')
    expect(fields[0].format).toBe('url')
    expect(fields[1].key).toBe('timeout')
    expect(fields[1].default).toBe(30)
  })

  it('handles simple format: array of strings → dropdown', () => {
    const schema = {
      browser: ['chrome', 'firefox', 'safari']
    }

    const fields = parseParamsSchema(schema)
    expect(fields).toHaveLength(1)
    expect(fields[0].options).toHaveLength(3)
    expect(fields[0].options[0]).toEqual({ value: 'chrome', label: 'chrome' })
    expect(fields[0].default).toBe('chrome')
  })

  it('handles simple format: boolean value', () => {
    const schema = {
      headless: true
    }

    const fields = parseParamsSchema(schema)
    expect(fields).toHaveLength(1)
    expect(fields[0].type).toBe('boolean')
    expect(fields[0].default).toBe(true)
  })

  it('handles simple format: number value', () => {
    const schema = {
      retries: 3
    }

    const fields = parseParamsSchema(schema)
    expect(fields).toHaveLength(1)
    expect(fields[0].type).toBe('number')
    expect(fields[0].default).toBe(3)
  })

  it('handles simple format: string value', () => {
    const schema = {
      selector: '.main'
    }

    const fields = parseParamsSchema(schema)
    expect(fields).toHaveLength(1)
    expect(fields[0].type).toBe('string')
    expect(fields[0].default).toBe('.main')
  })

  it('marks hidden fields', () => {
    const schema = {
      type: 'object',
      properties: {
        visible: { type: 'string', label: 'Visible' },
        secret: { type: 'string', label: 'Secret', hidden: true }
      }
    }

    const fields = parseParamsSchema(schema)
    expect(fields[0].hidden).toBe(false)
    expect(fields[1].hidden).toBe(true)
  })

  it('marks expert/advanced fields', () => {
    const schema = {
      type: 'object',
      properties: {
        basic: { type: 'string', label: 'Basic' },
        advanced: { type: 'string', label: 'Advanced', advanced: true },
        expert: { type: 'string', label: 'Expert', visibility: 'expert' }
      }
    }

    const fields = parseParamsSchema(schema)
    expect(fields[0].expert).toBe(false)
    expect(fields[1].expert).toBe(true)
    expect(fields[2].expert).toBe(true)
  })

  it('preserves displayOptions for conditional visibility', () => {
    const schema = {
      type: 'object',
      properties: {
        mode: { type: 'string', label: 'Mode', enum: ['simple', 'advanced'] },
        detail: {
          type: 'string',
          label: 'Detail',
          displayOptions: {
            show: { mode: ['advanced'] }
          }
        }
      }
    }

    const fields = parseParamsSchema(schema)
    expect(fields[1].displayOptions).toEqual({ show: { mode: ['advanced'] } })
  })

  it('preserves showIf/hideIf conditions', () => {
    const schema = {
      type: 'object',
      properties: {
        field: {
          type: 'string',
          label: 'Field',
          showIf: { mode: ['advanced'] },
          hideIf: { disabled: [true] }
        }
      }
    }

    const fields = parseParamsSchema(schema)
    expect(fields[0].showIf).toEqual({ mode: ['advanced'] })
    expect(fields[0].hideIf).toEqual({ disabled: [true] })
  })

  it('handles enum options', () => {
    const schema = {
      type: 'object',
      properties: {
        method: { type: 'string', enum: ['GET', 'POST', 'PUT', 'DELETE'] }
      }
    }

    const fields = parseParamsSchema(schema)
    expect(fields[0].options).toHaveLength(4)
    expect(fields[0].options[0]).toEqual({ value: 'GET', label: 'GET' })
  })

  it('handles object options', () => {
    const schema = {
      type: 'object',
      properties: {
        size: {
          type: 'string',
          options: [
            { value: 'sm', label: 'Small' },
            { value: 'lg', label: 'Large' }
          ]
        }
      }
    }

    const fields = parseParamsSchema(schema)
    expect(fields[0].options).toHaveLength(2)
    expect(fields[0].options[0]).toEqual({ value: 'sm', label: 'Small' })
  })

  it('preserves array items schema', () => {
    const schema = {
      type: 'object',
      properties: {
        tags: {
          type: 'array',
          items: { type: 'string' },
          minItems: 1,
          maxItems: 10
        }
      }
    }

    const fields = parseParamsSchema(schema)
    expect(fields[0].items).toEqual({ type: 'string' })
    expect(fields[0].minItems).toBe(1)
    expect(fields[0].maxItems).toBe(10)
  })

  it('preserves nested object properties', () => {
    const schema = {
      type: 'object',
      properties: {
        config: {
          type: 'object',
          properties: {
            host: { type: 'string' },
            port: { type: 'number' }
          }
        }
      }
    }

    const fields = parseParamsSchema(schema)
    expect(fields[0].properties).toHaveProperty('host')
    expect(fields[0].properties).toHaveProperty('port')
  })

  it('computes smart step for slider ranges', () => {
    const schema = {
      type: 'object',
      properties: {
        temperature: { type: 'number', min: 0, max: 1 },
        retries: { type: 'number', min: 0, max: 5 },
        timeout: { type: 'number', min: 0, max: 300 }
      }
    }

    const fields = parseParamsSchema(schema)
    expect(fields[0].step).toBe(0.01)  // range <= 1
    expect(fields[1].step).toBe(0.1)   // range <= 10
    expect(fields[2].step).toBe(1)     // range > 10
  })

  it('preserves widget and ui config', () => {
    const schema = {
      type: 'object',
      properties: {
        element: {
          type: 'string',
          widget: 'element_picker',
          ui: { widget: 'element_picker', element_types: ['button', 'input'] }
        }
      }
    }

    const fields = parseParamsSchema(schema)
    expect(fields[0].widget).toBe('element_picker')
    expect(fields[0].ui.element_types).toEqual(['button', 'input'])
  })
})

describe('parseOutputSchema', () => {
  it('returns empty array for null/undefined schema', () => {
    expect(parseOutputSchema(null)).toEqual([])
    expect(parseOutputSchema(undefined)).toEqual([])
  })

  it('parses output fields', () => {
    const schema = {
      result: { type: 'string', label: 'Result', description: 'Output text' },
      count: { type: 'number', label: 'Count' }
    }

    const fields = parseOutputSchema(schema)
    expect(fields).toHaveLength(2)
    expect(fields[0].key).toBe('result')
    expect(fields[0].label).toBe('Result')
    expect(fields[0].primary).toBe(true)  // key === 'result'
    expect(fields[1].key).toBe('count')
    expect(fields[1].primary).toBe(false)
  })

  it('detects primary from explicit flag', () => {
    const schema = {
      data: { type: 'object', label: 'Data', primary: true }
    }

    const fields = parseOutputSchema(schema)
    expect(fields[0].primary).toBe(true)
  })

  it('assigns correct widget types', () => {
    const schema = {
      text: { type: 'string' },
      num: { type: 'number' },
      flag: { type: 'boolean' },
      items: { type: 'array' },
      obj: { type: 'object' }
    }

    const fields = parseOutputSchema(schema)
    expect(fields[0].widgetType).toBe('text-block')
    expect(fields[1].widgetType).toBe('number-display')
    expect(fields[2].widgetType).toBe('status-badge')
    expect(fields[3].widgetType).toBe('table-view')
    expect(fields[4].widgetType).toBe('json-viewer')
  })
})
