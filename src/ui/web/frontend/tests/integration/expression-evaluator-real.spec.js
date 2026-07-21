/**
 * Integration Test: ExpressionEvaluator (100% real, zero mocks)
 *
 * Tests the REAL ExpressionEvaluator with no mocks whatsoever.
 * All expression parsing, resolution, interpolation, and
 * error handling runs through real production code.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock only the dev-mode backend comparison (network call)
// The evaluator itself is 100% real
vi.mock('@/api/expression', () => ({
  expressionAPI: { evaluate: vi.fn() },
  default: { evaluate: vi.fn() }
}))

vi.mock('@/utils/environment', () => ({
  isDevelopment: () => false
}))

import { ExpressionEvaluator, createEvaluator, evaluate } from '@/services/ExpressionEvaluator'

describe('ExpressionEvaluator (100% Real)', () => {
  let evaluator

  beforeEach(() => {
    evaluator = new ExpressionEvaluator({
      inputs: {
        name: 'Alice',
        age: 30,
        email: 'alice@flyto2.com',
        items: ['apple', 'banana', 'cherry'],
        address: {
          city: 'Taipei',
          zip: '10001',
          coords: { lat: 25.033, lng: 121.565 }
        },
        isActive: true,
        count: 0,
        emptyString: ''
      },
      steps: {
        scrape: {
          result: 'Hello World',
          data: { title: 'Page Title', links: ['https://a.flyto2.com', 'https://b.flyto2.com'] },
          status: 200
        },
        transform: {
          output: { processed: true, count: 42 }
        }
      },
      env: {
        API_KEY: 'sk-secret-123',
        BASE_URL: 'https://api.flyto2.com',
        DEBUG: 'true'
      }
    })
  })

  // =========================================================================
  // Single expression resolution
  // =========================================================================

  describe('single expression evaluation', () => {
    it('should resolve UI input values', () => {
      expect(evaluator.evaluateSingle('${ui.inputs.name}')).toEqual({ ok: true, value: 'Alice' })
      expect(evaluator.evaluateSingle('${ui.inputs.age}')).toEqual({ ok: true, value: 30 })
      expect(evaluator.evaluateSingle('${ui.inputs.isActive}')).toEqual({ ok: true, value: true })
    })

    it('should resolve step output values', () => {
      expect(evaluator.evaluateSingle('${steps.scrape.result}')).toEqual({ ok: true, value: 'Hello World' })
      expect(evaluator.evaluateSingle('${steps.scrape.status}')).toEqual({ ok: true, value: 200 })
    })

    it('should resolve environment variables', () => {
      expect(evaluator.evaluateSingle('${env.API_KEY}')).toEqual({ ok: true, value: 'sk-secret-123' })
      expect(evaluator.evaluateSingle('${env.BASE_URL}')).toEqual({ ok: true, value: 'https://api.flyto2.com' })
    })

    it('should resolve nested object paths', () => {
      expect(evaluator.evaluateSingle('${ui.inputs.address.city}')).toEqual({ ok: true, value: 'Taipei' })
      expect(evaluator.evaluateSingle('${ui.inputs.address.coords.lat}')).toEqual({ ok: true, value: 25.033 })
    })

    it('should resolve nested step output paths', () => {
      expect(evaluator.evaluateSingle('${steps.scrape.data.title}')).toEqual({ ok: true, value: 'Page Title' })
      expect(evaluator.evaluateSingle('${steps.transform.output.count}')).toEqual({ ok: true, value: 42 })
    })

    it('should return arrays as-is', () => {
      const result = evaluator.evaluateSingle('${ui.inputs.items}')
      expect(result.ok).toBe(true)
      expect(result.value).toEqual(['apple', 'banana', 'cherry'])
    })

    it('should return objects as-is', () => {
      const result = evaluator.evaluateSingle('${steps.transform.output}')
      expect(result.ok).toBe(true)
      expect(result.value).toEqual({ processed: true, count: 42 })
    })

    it('should handle falsy values correctly', () => {
      expect(evaluator.evaluateSingle('${ui.inputs.count}')).toEqual({ ok: true, value: 0 })
      expect(evaluator.evaluateSingle('${ui.inputs.emptyString}')).toEqual({ ok: true, value: '' })
      expect(evaluator.evaluateSingle('${ui.inputs.isActive}')).toEqual({ ok: true, value: true })
    })

    it('should return non-expression strings as-is', () => {
      expect(evaluator.evaluateSingle('just a string')).toEqual({ ok: true, value: 'just a string' })
      expect(evaluator.evaluateSingle('')).toEqual({ ok: true, value: '' })
    })
  })

  // =========================================================================
  // Missing variables
  // =========================================================================

  describe('missing variables', () => {
    it('should report missing input variables', () => {
      const result = evaluator.evaluateSingle('${ui.inputs.nonexistent}')
      expect(result.ok).toBe(false)
      expect(result.error).toContain('Variable not found')
      expect(result.missingVars).toContain('${ui.inputs.nonexistent}')
    })

    it('should report missing step variables', () => {
      const result = evaluator.evaluateSingle('${steps.missing.output}')
      expect(result.ok).toBe(false)
      expect(result.error).toContain('Variable not found')
    })

    it('should report missing env variables', () => {
      const result = evaluator.evaluateSingle('${env.MISSING_KEY}')
      expect(result.ok).toBe(false)
      expect(result.missingVars).toContain('${env.MISSING_KEY}')
    })

    it('should report invalid expression format', () => {
      const result = evaluator.evaluateSingle('${invalid}')
      expect(result.ok).toBe(false)
      expect(result.error).toBeDefined()
    })
  })

  // =========================================================================
  // Template interpolation
  // =========================================================================

  describe('template interpolation', () => {
    it('should interpolate single variable in string', () => {
      const result = evaluator.evaluateTemplate('Hello ${ui.inputs.name}!')
      expect(result.ok).toBe(true)
      expect(result.value).toBe('Hello Alice!')
    })

    it('should interpolate multiple variables', () => {
      const result = evaluator.evaluateTemplate('Name: ${ui.inputs.name}, Age: ${ui.inputs.age}')
      expect(result.ok).toBe(true)
      expect(result.value).toBe('Name: Alice, Age: 30')
    })

    it('should interpolate variables from different sources', () => {
      const result = evaluator.evaluateTemplate(
        'User: ${ui.inputs.name}, Result: ${steps.scrape.result}, Key: ${env.API_KEY}'
      )
      expect(result.ok).toBe(true)
      expect(result.value).toBe('User: Alice, Result: Hello World, Key: sk-secret-123')
    })

    it('should stringify objects in interpolation', () => {
      const result = evaluator.evaluateTemplate('Data: ${steps.transform.output}')
      expect(result.ok).toBe(true)
      expect(result.value).toBe('Data: {"processed":true,"count":42}')
    })

    it('should keep unresolved expressions as-is', () => {
      const result = evaluator.evaluateTemplate('Hello ${ui.inputs.missing}!')
      expect(result.ok).toBe(false)
      expect(result.value).toBe('Hello ${ui.inputs.missing}!')
      expect(result.missingVars).toContain('${ui.inputs.missing}')
    })

    it('should handle pure expression (return typed value)', () => {
      const result = evaluator.evaluateTemplate('${ui.inputs.age}')
      expect(result.ok).toBe(true)
      expect(result.value).toBe(30)
      expect(typeof result.value).toBe('number')
    })

    it('should return non-expression strings unchanged', () => {
      expect(evaluator.evaluateTemplate('plain text')).toEqual({ ok: true, value: 'plain text' })
    })

    it('should handle non-string input', () => {
      expect(evaluator.evaluateTemplate(42)).toEqual({ ok: true, value: 42 })
      expect(evaluator.evaluateTemplate(null)).toEqual({ ok: true, value: null })
      expect(evaluator.evaluateTemplate(true)).toEqual({ ok: true, value: true })
    })
  })

  // =========================================================================
  // evaluate() — handles objects, arrays, primitives
  // =========================================================================

  describe('evaluate (recursive)', () => {
    it('should evaluate null/undefined passthrough', () => {
      expect(evaluator.evaluate(null)).toEqual({ ok: true, value: null })
      expect(evaluator.evaluate(undefined)).toEqual({ ok: true, value: undefined })
    })

    it('should evaluate primitive passthrough', () => {
      expect(evaluator.evaluate(42)).toEqual({ ok: true, value: 42 })
      expect(evaluator.evaluate(true)).toEqual({ ok: true, value: true })
      expect(evaluator.evaluate(3.14)).toEqual({ ok: true, value: 3.14 })
    })

    it('should evaluate array elements', () => {
      const result = evaluator.evaluate([
        '${ui.inputs.name}',
        '${ui.inputs.age}',
        'literal',
        42
      ])
      expect(result.ok).toBe(true)
      expect(result.value).toEqual(['Alice', 30, 'literal', 42])
    })

    it('should evaluate object values recursively', () => {
      const result = evaluator.evaluate({
        greeting: 'Hello ${ui.inputs.name}',
        url: '${env.BASE_URL}/api',
        data: {
          nested: '${steps.scrape.result}',
          literal: 'unchanged'
        }
      })
      expect(result.ok).toBe(true)
      expect(result.value).toEqual({
        greeting: 'Hello Alice',
        url: 'https://api.flyto2.com/api',
        data: {
          nested: 'Hello World',
          literal: 'unchanged'
        }
      })
    })

    it('should report errors in array evaluation', () => {
      const result = evaluator.evaluate(['${ui.inputs.name}', '${ui.inputs.missing}'])
      expect(result.ok).toBe(false)
      expect(result.value[0]).toBe('Alice')
      expect(result.missingVars).toContain('${ui.inputs.missing}')
    })

    it('should report errors in object evaluation', () => {
      const result = evaluator.evaluate({
        valid: '${ui.inputs.name}',
        invalid: '${ui.inputs.missing}'
      })
      expect(result.ok).toBe(false)
      expect(result.value.valid).toBe('Alice')
      expect(result.missingVars).toContain('${ui.inputs.missing}')
    })
  })

  // =========================================================================
  // Context management
  // =========================================================================

  describe('context management', () => {
    it('should update context with new values', () => {
      evaluator.updateContext({
        inputs: { newField: 'newValue' }
      })

      const result = evaluator.evaluateSingle('${ui.inputs.newField}')
      expect(result).toEqual({ ok: true, value: 'newValue' })

      // Original values should still work
      expect(evaluator.evaluateSingle('${ui.inputs.name}')).toEqual({ ok: true, value: 'Alice' })
    })

    it('should set step result', () => {
      evaluator.setStepResult('newStep', { output: 'stepData' })

      const result = evaluator.evaluateSingle('${steps.newStep.output}')
      expect(result).toEqual({ ok: true, value: 'stepData' })
    })

    it('should set individual input', () => {
      evaluator.setInput('dynamicField', 'dynamicValue')

      const result = evaluator.evaluateSingle('${ui.inputs.dynamicField}')
      expect(result).toEqual({ ok: true, value: 'dynamicValue' })
    })
  })

  // =========================================================================
  // validate()
  // =========================================================================

  describe('validate', () => {
    it('should validate resolvable expressions', () => {
      const result = evaluator.validate('${ui.inputs.name}')
      expect(result.valid).toBe(true)
      expect(result.missing).toEqual([])
    })

    it('should identify missing variables', () => {
      const result = evaluator.validate('Hello ${ui.inputs.missing}!')
      expect(result.valid).toBe(false)
      expect(result.missing).toContain('${ui.inputs.missing}')
    })

    it('should validate complex objects', () => {
      const result = evaluator.validate({
        a: '${ui.inputs.name}',
        b: '${steps.scrape.result}'
      })
      expect(result.valid).toBe(true)
    })
  })

  // =========================================================================
  // extractExpressions (static)
  // =========================================================================

  describe('extractExpressions (static)', () => {
    it('should extract expressions from string', () => {
      const exprs = ExpressionEvaluator.extractExpressions(
        'Hello ${ui.inputs.name}, your API key is ${env.API_KEY}'
      )
      expect(exprs).toContain('${ui.inputs.name}')
      expect(exprs).toContain('${env.API_KEY}')
      expect(exprs).toHaveLength(2)
    })

    it('should extract from nested objects', () => {
      const exprs = ExpressionEvaluator.extractExpressions({
        a: '${ui.inputs.name}',
        b: { c: '${steps.scrape.result}' },
        d: ['${env.API_KEY}', 'literal']
      })
      expect(exprs).toHaveLength(3)
    })

    it('should deduplicate expressions', () => {
      const exprs = ExpressionEvaluator.extractExpressions(
        '${ui.inputs.name} and ${ui.inputs.name}'
      )
      expect(exprs).toHaveLength(1)
    })

    it('should return empty array for no expressions', () => {
      expect(ExpressionEvaluator.extractExpressions('plain text')).toEqual([])
      expect(ExpressionEvaluator.extractExpressions(42)).toEqual([])
      expect(ExpressionEvaluator.extractExpressions(null)).toEqual([])
    })
  })

  // =========================================================================
  // getAvailableVariables
  // =========================================================================

  describe('getAvailableVariables', () => {
    it('should return all available variables with metadata', () => {
      const vars = evaluator.getAvailableVariables()

      // Inputs
      expect(vars.inputs.length).toBeGreaterThan(0)
      const nameVar = vars.inputs.find(v => v.label === 'name')
      expect(nameVar).toBeDefined()
      expect(nameVar.expression).toBe('${ui.inputs.name}')
      expect(nameVar.value).toBe('Alice')
      expect(nameVar.dataType).toBe('string')

      const ageVar = vars.inputs.find(v => v.label === 'age')
      expect(ageVar.dataType).toBe('number')

      const itemsVar = vars.inputs.find(v => v.label === 'items')
      expect(itemsVar.dataType).toBe('array')

      const addressVar = vars.inputs.find(v => v.label === 'address')
      expect(addressVar.dataType).toBe('object')

      const boolVar = vars.inputs.find(v => v.label === 'isActive')
      expect(boolVar.dataType).toBe('boolean')

      // Steps
      expect(vars.steps.length).toBeGreaterThan(0)
      const scrapeResult = vars.steps.find(v => v.label === 'scrape.result')
      expect(scrapeResult).toBeDefined()
      expect(scrapeResult.expression).toBe('${steps.scrape.result}')

      // Env
      expect(vars.env.length).toBeGreaterThan(0)
      const apiKey = vars.env.find(v => v.label === 'API_KEY')
      expect(apiKey).toBeDefined()
      expect(apiKey.dataType).toBe('string')
    })
  })

  // =========================================================================
  // Helper functions
  // =========================================================================

  describe('createEvaluator helper', () => {
    it('should create a function that evaluates expressions', () => {
      const eval_ = createEvaluator({
        inputs: { x: 10 },
        steps: {},
        env: {}
      })

      const result = eval_('${ui.inputs.x}')
      expect(result).toEqual({ ok: true, value: 10 })
    })
  })

  describe('evaluate helper', () => {
    it('should return value directly on success', () => {
      const result = evaluate('${ui.inputs.name}', {
        inputs: { name: 'Bob' },
        steps: {},
        env: {}
      })
      expect(result).toBe('Bob')
    })

    it('should throw on missing variable', () => {
      expect(() => evaluate('${ui.inputs.missing}', {
        inputs: {},
        steps: {},
        env: {}
      })).toThrow('Variable not found')
    })
  })

  // =========================================================================
  // Edge cases
  // =========================================================================

  describe('edge cases', () => {
    it('should handle empty context', () => {
      const emptyEval = new ExpressionEvaluator()
      expect(emptyEval.evaluateSingle('${ui.inputs.anything}').ok).toBe(false)
      expect(emptyEval.evaluate('no expressions')).toEqual({ ok: true, value: 'no expressions' })
    })

    it('should handle deeply nested paths that end in undefined', () => {
      const result = evaluator.evaluateSingle('${ui.inputs.address.coords.nonexistent}')
      expect(result.ok).toBe(false)
    })

    it('should handle path traversal through non-object', () => {
      // age is a number, can't traverse further
      const result = evaluator.evaluateSingle('${ui.inputs.age.something}')
      expect(result.ok).toBe(false)
    })
  })
})
