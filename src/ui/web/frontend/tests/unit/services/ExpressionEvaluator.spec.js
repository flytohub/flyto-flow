/**
 * ExpressionEvaluator Unit Tests
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock dependencies before importing
vi.mock('@/constants/templateBuilder/bindingTypes', () => {
  const VARIABLE_SOURCES = Object.freeze({
    UI_INPUTS: 'ui.inputs',
    STEPS: 'steps',
    ENV: 'env'
  })

  const VARIABLE_PATTERN = /\$\{([^}]+)\}/g
  const SINGLE_VARIABLE_PATTERN = /^\$\{([^}]+)\}$/

  const BindingUtils = Object.freeze({
    parseExpression(expression) {
      const match = expression.match(SINGLE_VARIABLE_PATTERN)
      if (!match) return null

      const fullPath = match[1]
      const parts = fullPath.split('.')
      if (parts.length < 2) return null

      let source, path
      if (parts[0] === 'ui' && parts[1] === 'inputs') {
        source = VARIABLE_SOURCES.UI_INPUTS
        path = parts.slice(2)
      } else if (parts[0] === 'steps') {
        source = VARIABLE_SOURCES.STEPS
        path = parts.slice(1)
      } else if (parts[0] === 'env') {
        source = VARIABLE_SOURCES.ENV
        path = parts.slice(1)
      } else {
        return null
      }
      return { source, path, fullPath }
    },
    isExpression(value) {
      return typeof value === 'string' && SINGLE_VARIABLE_PATTERN.test(value)
    },
    containsExpression(value) {
      if (typeof value !== 'string') return false
      // Reset lastIndex since VARIABLE_PATTERN has global flag
      VARIABLE_PATTERN.lastIndex = 0
      return VARIABLE_PATTERN.test(value)
    }
  })

  return { VARIABLE_PATTERN, SINGLE_VARIABLE_PATTERN, VARIABLE_SOURCES, BindingUtils }
})

vi.mock('@/utils/environment', () => ({
  isDevelopment: vi.fn(() => false)
}))

vi.mock('@/api/expression', () => ({
  expressionAPI: {
    evaluate: vi.fn()
  }
}))

import {
  ExpressionEvaluator,
  createEvaluator,
  evaluate,
  setDevComparisonEnabled
} from '@/services/ExpressionEvaluator'

describe('ExpressionEvaluator', () => {
  let evaluator

  beforeEach(() => {
    evaluator = new ExpressionEvaluator({
      inputs: { name: 'Alice', age: 30 },
      steps: { crop: { result: 'cropped.png', width: 100 } },
      env: { API_KEY: 'sk-123' }
    })
  })

  // =========================================================================
  // Constructor and context
  // =========================================================================

  describe('constructor', () => {
    it('should initialize with default empty context', () => {
      const e = new ExpressionEvaluator()
      expect(e.context).toEqual({ inputs: {}, steps: {}, env: {} })
    })

    it('should initialize with provided context', () => {
      expect(evaluator.context.inputs.name).toBe('Alice')
      expect(evaluator.context.steps.crop.result).toBe('cropped.png')
      expect(evaluator.context.env.API_KEY).toBe('sk-123')
    })
  })

  describe('updateContext', () => {
    it('should merge inputs', () => {
      evaluator.updateContext({ inputs: { email: 'a@flyto2.com' } })
      expect(evaluator.context.inputs.name).toBe('Alice')
      expect(evaluator.context.inputs.email).toBe('a@flyto2.com')
    })

    it('should merge steps', () => {
      evaluator.updateContext({ steps: { resize: { output: 'resized.png' } } })
      expect(evaluator.context.steps.crop).toBeDefined()
      expect(evaluator.context.steps.resize.output).toBe('resized.png')
    })

    it('should merge env', () => {
      evaluator.updateContext({ env: { SECRET: 'abc' } })
      expect(evaluator.context.env.API_KEY).toBe('sk-123')
      expect(evaluator.context.env.SECRET).toBe('abc')
    })

    it('should skip keys not provided', () => {
      evaluator.updateContext({})
      expect(evaluator.context.inputs.name).toBe('Alice')
    })
  })

  describe('setStepResult', () => {
    it('should set step outputs', () => {
      evaluator.setStepResult('upload', { url: 'https://flyto2.com' })
      expect(evaluator.context.steps.upload.url).toBe('https://flyto2.com')
    })
  })

  describe('setInput', () => {
    it('should set input value', () => {
      evaluator.setInput('color', 'blue')
      expect(evaluator.context.inputs.color).toBe('blue')
    })
  })

  // =========================================================================
  // evaluateSingle
  // =========================================================================

  describe('evaluateSingle', () => {
    it('should return plain text as-is', () => {
      const result = evaluator.evaluateSingle('hello')
      expect(result).toEqual({ ok: true, value: 'hello' })
    })

    it('should resolve ui.inputs expression', () => {
      const result = evaluator.evaluateSingle('${ui.inputs.name}')
      expect(result).toEqual({ ok: true, value: 'Alice' })
    })

    it('should resolve steps expression', () => {
      const result = evaluator.evaluateSingle('${steps.crop.result}')
      expect(result).toEqual({ ok: true, value: 'cropped.png' })
    })

    it('should resolve env expression', () => {
      const result = evaluator.evaluateSingle('${env.API_KEY}')
      expect(result).toEqual({ ok: true, value: 'sk-123' })
    })

    it('should return error for missing variable', () => {
      const result = evaluator.evaluateSingle('${ui.inputs.missing}')
      expect(result.ok).toBe(false)
      expect(result.missingVars).toContain('${ui.inputs.missing}')
    })

    it('should return error for invalid expression', () => {
      const result = evaluator.evaluateSingle('${invalid}')
      expect(result.ok).toBe(false)
    })
  })

  // =========================================================================
  // evaluateTemplate
  // =========================================================================

  describe('evaluateTemplate', () => {
    it('should return non-string values as-is', () => {
      const result = evaluator.evaluateTemplate(42)
      expect(result).toEqual({ ok: true, value: 42 })
    })

    it('should return pure expression as typed value', () => {
      const result = evaluator.evaluateTemplate('${ui.inputs.age}')
      expect(result).toEqual({ ok: true, value: 30 })
    })

    it('should interpolate mixed template', () => {
      const result = evaluator.evaluateTemplate('Hello ${ui.inputs.name}!')
      expect(result).toEqual({ ok: true, value: 'Hello Alice!' })
    })

    it('should interpolate multiple expressions', () => {
      const result = evaluator.evaluateTemplate('${ui.inputs.name} is ${ui.inputs.age}')
      expect(result).toEqual({ ok: true, value: 'Alice is 30' })
    })

    it('should return string without expressions as-is', () => {
      const result = evaluator.evaluateTemplate('no expressions here')
      expect(result).toEqual({ ok: true, value: 'no expressions here' })
    })

    it('should keep original expression on missing variable in template', () => {
      const result = evaluator.evaluateTemplate('Hello ${ui.inputs.missing}!')
      expect(result.ok).toBe(false)
      expect(result.value).toBe('Hello ${ui.inputs.missing}!')
      expect(result.missingVars).toContain('${ui.inputs.missing}')
    })

    it('should stringify objects in interpolation', () => {
      evaluator.setInput('data', { foo: 'bar' })
      const result = evaluator.evaluateTemplate('Data: ${ui.inputs.data}')
      expect(result.ok).toBe(true)
      expect(result.value).toBe('Data: {"foo":"bar"}')
    })

    it('should convert null to empty string in interpolation', () => {
      evaluator.setInput('empty', null)
      const result = evaluator.evaluateTemplate('Value: ${ui.inputs.empty}')
      expect(result.ok).toBe(true)
      expect(result.value).toBe('Value: ')
    })
  })

  // =========================================================================
  // evaluate (generic)
  // =========================================================================

  describe('evaluate', () => {
    it('should passthrough null', () => {
      expect(evaluator.evaluate(null)).toEqual({ ok: true, value: null })
    })

    it('should passthrough undefined', () => {
      expect(evaluator.evaluate(undefined)).toEqual({ ok: true, value: undefined })
    })

    it('should passthrough numbers', () => {
      expect(evaluator.evaluate(42)).toEqual({ ok: true, value: 42 })
    })

    it('should passthrough booleans', () => {
      expect(evaluator.evaluate(true)).toEqual({ ok: true, value: true })
    })

    it('should evaluate string values', () => {
      const result = evaluator.evaluate('${ui.inputs.name}')
      expect(result).toEqual({ ok: true, value: 'Alice' })
    })

    it('should evaluate arrays', () => {
      const result = evaluator.evaluate(['${ui.inputs.name}', 'literal'])
      expect(result).toEqual({ ok: true, value: ['Alice', 'literal'] })
    })

    it('should report errors in arrays', () => {
      const result = evaluator.evaluate(['${ui.inputs.missing}', 'ok'])
      expect(result.ok).toBe(false)
      expect(result.value).toEqual([undefined, 'ok'])
    })

    it('should evaluate objects', () => {
      const result = evaluator.evaluate({
        greeting: 'Hello ${ui.inputs.name}!',
        key: '${env.API_KEY}'
      })
      expect(result).toEqual({
        ok: true,
        value: { greeting: 'Hello Alice!', key: 'sk-123' }
      })
    })

    it('should report errors in objects', () => {
      const result = evaluator.evaluate({
        good: '${ui.inputs.name}',
        bad: '${ui.inputs.missing}'
      })
      expect(result.ok).toBe(false)
      expect(result.value.good).toBe('Alice')
    })
  })

  // =========================================================================
  // validate
  // =========================================================================

  describe('validate', () => {
    it('should return valid for resolvable expression', () => {
      const result = evaluator.validate('${ui.inputs.name}')
      expect(result).toEqual({ valid: true, missing: [] })
    })

    it('should return invalid with missing vars', () => {
      const result = evaluator.validate('${ui.inputs.missing}')
      expect(result.valid).toBe(false)
      expect(result.missing).toContain('${ui.inputs.missing}')
    })
  })

  // =========================================================================
  // extractExpressions (static)
  // =========================================================================

  describe('extractExpressions', () => {
    it('should extract expressions from string', () => {
      const result = ExpressionEvaluator.extractExpressions('${ui.inputs.name} and ${env.KEY}')
      expect(result).toContain('${ui.inputs.name}')
      expect(result).toContain('${env.KEY}')
    })

    it('should extract from nested arrays', () => {
      const result = ExpressionEvaluator.extractExpressions(['${ui.inputs.a}', ['${env.B}']])
      expect(result).toContain('${ui.inputs.a}')
      expect(result).toContain('${env.B}')
    })

    it('should extract from objects', () => {
      const result = ExpressionEvaluator.extractExpressions({ key: '${steps.x.y}' })
      expect(result).toContain('${steps.x.y}')
    })

    it('should return empty for non-expression values', () => {
      expect(ExpressionEvaluator.extractExpressions(42)).toEqual([])
      expect(ExpressionEvaluator.extractExpressions(null)).toEqual([])
    })

    it('should deduplicate expressions', () => {
      const result = ExpressionEvaluator.extractExpressions('${ui.inputs.a} ${ui.inputs.a}')
      expect(result).toHaveLength(1)
    })
  })

  // =========================================================================
  // getAvailableVariables
  // =========================================================================

  describe('getAvailableVariables', () => {
    it('should list inputs', () => {
      const vars = evaluator.getAvailableVariables()
      expect(vars.inputs).toHaveLength(2)
      expect(vars.inputs[0].path).toBe('ui.inputs.name')
      expect(vars.inputs[0].dataType).toBe('string')
    })

    it('should list step outputs', () => {
      const vars = evaluator.getAvailableVariables()
      expect(vars.steps).toHaveLength(2)
      expect(vars.steps[0].path).toBe('steps.crop.result')
    })

    it('should list env variables', () => {
      const vars = evaluator.getAvailableVariables()
      expect(vars.env).toHaveLength(1)
      expect(vars.env[0].path).toBe('env.API_KEY')
      expect(vars.env[0].dataType).toBe('string')
    })
  })

  // =========================================================================
  // _inferType
  // =========================================================================

  describe('_inferType', () => {
    it('should detect types correctly', () => {
      expect(evaluator._inferType(null)).toBe('any')
      expect(evaluator._inferType(undefined)).toBe('any')
      expect(evaluator._inferType('hello')).toBe('string')
      expect(evaluator._inferType(42)).toBe('number')
      expect(evaluator._inferType(true)).toBe('boolean')
      expect(evaluator._inferType([1, 2])).toBe('array')
      expect(evaluator._inferType({ a: 1 })).toBe('object')
    })
  })

  // =========================================================================
  // Helper exports
  // =========================================================================

  describe('createEvaluator', () => {
    it('should return an evaluate function', () => {
      const evalFn = createEvaluator({ inputs: { x: 10 } })
      const result = evalFn('${ui.inputs.x}')
      expect(result).toEqual({ ok: true, value: 10 })
    })
  })

  describe('evaluate helper', () => {
    it('should return resolved value', () => {
      const val = evaluate('${ui.inputs.name}', { inputs: { name: 'Bob' } })
      expect(val).toBe('Bob')
    })

    it('should throw on error', () => {
      expect(() => evaluate('${ui.inputs.missing}', { inputs: {} })).toThrow()
    })
  })

  describe('setDevComparisonEnabled', () => {
    it('should be callable without error', () => {
      expect(() => setDevComparisonEnabled(false)).not.toThrow()
      expect(() => setDevComparisonEnabled(true)).not.toThrow()
    })
  })
})
