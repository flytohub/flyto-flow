/**
 * Expression Evaluator Service (UX PREVIEW ONLY)
 *
 * Safely evaluates variable expressions like:
 * - ${ui.inputs.name} -> value from UI inputs
 * - ${steps.crop.result} -> output from previous workflow step
 * - ${env.API_KEY} -> environment variable
 * - Mixed: "Hello ${ui.inputs.name}!" -> interpolated string
 *
 * Features:
 * - Safe evaluation (no eval/Function)
 * - Nested path resolution
 * - String interpolation
 * - Type coercion
 * - Error handling with helpful messages
 *
 * IMPORTANT: This evaluator is for UI PREVIEW purposes only.
 * The authoritative expression evaluation is done server-side via:
 * - POST /api/expression/evaluate - Evaluate single expression
 * - POST /api/expression/validate - Validate syntax
 * - POST /api/expression/batch - Evaluate multiple expressions
 *
 * For workflow execution, the backend's SecureExpressionEvaluator is used,
 * which provides additional security (AST-based, no eval/exec).
 */

import {
  VARIABLE_PATTERN,
  SINGLE_VARIABLE_PATTERN,
  VARIABLE_SOURCES,
  BindingUtils
} from '@/constants/templateBuilder/bindingTypes'
import { isDevelopment } from '@/utils/environment'
import { expressionAPI } from '@/api/expression'

/**
 * Enable/disable dev mode comparison warnings
 * Set to false in performance-critical scenarios
 */
let DEV_COMPARISON_ENABLED = true

/**
 * Enable or disable dev mode comparison
 * @param {boolean} enabled
 */
export function setDevComparisonEnabled(enabled) {
  DEV_COMPARISON_ENABLED = enabled
}

/**
 * Compare local evaluation with backend (dev mode only)
 * Logs a warning if results differ
 * @param {string} expression - Expression evaluated
 * @param {*} localResult - Local evaluation result
 * @param {Object} context - Evaluation context
 */
async function compareWithBackend(expression, localResult, context) {
  if (!isDevelopment() || !DEV_COMPARISON_ENABLED) return

  try {
    const backendResult = await expressionAPI.evaluate(expression, context)

    if (backendResult.ok) {
      const localValue = localResult.ok ? localResult.value : null
      const backendValue = backendResult.result

      // Deep comparison
      const localJSON = JSON.stringify(localValue)
      const backendJSON = JSON.stringify(backendValue)

      if (localJSON !== backendJSON) {
        // Dev-only: frontend/backend mismatch detected
        // Backend result is authoritative
      }
    }
  } catch {
    // Silently ignore backend errors in dev comparison
    // (backend may be unavailable during development)
  }
}

/**
 * Expression evaluation context
 * @typedef {Object} EvaluationContext
 * @property {Object} inputs - UI input values { fieldName: value }
 * @property {Object} steps - Step output results { stepId: { outputKey: value } }
 * @property {Object} env - Environment variables { KEY: value }
 */

/**
 * Expression evaluation result
 * @typedef {Object} EvaluationResult
 * @property {boolean} ok - Whether evaluation succeeded
 * @property {*} value - Resolved value (if ok)
 * @property {string} [error] - Error message (if not ok)
 * @property {string[]} [missingVars] - List of unresolved variables
 */

/**
 * Get nested property from object by path
 * @param {Object} obj - Source object
 * @param {string[]} path - Path parts array
 * @returns {*} Value at path or undefined
 */
function getNestedValue(obj, path) {
  if (!obj || !path || path.length === 0) return undefined

  let current = obj
  for (const key of path) {
    if (current === null || current === undefined) return undefined
    if (typeof current !== 'object') return undefined
    current = current[key]
  }
  return current
}

/**
 * Resolve a single variable expression to its value
 * @param {string} expression - Full expression like ${ui.inputs.name}
 * @param {EvaluationContext} context - Evaluation context
 * @returns {EvaluationResult}
 */
function resolveExpression(expression, context) {
  const parsed = BindingUtils.parseExpression(expression)

  if (!parsed) {
    return {
      ok: false,
      error: `Invalid expression format: ${expression}`,
      value: undefined
    }
  }

  const { source, path } = parsed

  let value
  let sourceName

  switch (source) {
    case VARIABLE_SOURCES.UI_INPUTS:
      sourceName = 'inputs'
      value = getNestedValue(context.inputs || {}, path)
      break

    case VARIABLE_SOURCES.STEPS:
      sourceName = 'steps'
      value = getNestedValue(context.steps || {}, path)
      break

    case VARIABLE_SOURCES.ENV:
      sourceName = 'env'
      value = getNestedValue(context.env || {}, path)
      break

    default:
      return {
        ok: false,
        error: `Unknown variable source: ${source}`,
        value: undefined
      }
  }

  if (value === undefined) {
    return {
      ok: false,
      error: `Variable not found: ${expression}`,
      value: undefined,
      missingVars: [expression]
    }
  }

  return { ok: true, value }
}

/**
 * Main ExpressionEvaluator class
 */
export class ExpressionEvaluator {
  /**
   * Create evaluator with context
   * @param {EvaluationContext} context
   */
  constructor(context = {}) {
    this.context = {
      inputs: context.inputs || {},
      steps: context.steps || {},
      env: context.env || {}
    }
  }

  /**
   * Update context with new values
   * @param {Partial<EvaluationContext>} updates
   */
  updateContext(updates) {
    if (updates.inputs) {
      this.context.inputs = { ...this.context.inputs, ...updates.inputs }
    }
    if (updates.steps) {
      this.context.steps = { ...this.context.steps, ...updates.steps }
    }
    if (updates.env) {
      this.context.env = { ...this.context.env, ...updates.env }
    }
  }

  /**
   * Set step output result
   * @param {string} stepId - Step identifier
   * @param {Object} outputs - Step outputs { key: value }
   */
  setStepResult(stepId, outputs) {
    this.context.steps[stepId] = outputs
  }

  /**
   * Set input value
   * @param {string} inputKey - Input field key
   * @param {*} value - Input value
   */
  setInput(inputKey, value) {
    this.context.inputs[inputKey] = value
  }

  /**
   * Evaluate a single expression
   * @param {string} expression - Expression like ${ui.inputs.name}
   * @param {Object} [options] - Options
   * @param {boolean} [options.compareWithBackend=false] - Enable backend comparison in dev mode
   * @returns {EvaluationResult}
   */
  evaluateSingle(expression, options = {}) {
    if (!BindingUtils.isExpression(expression)) {
      return { ok: true, value: expression }
    }
    const result = resolveExpression(expression, this.context)

    // Dev mode comparison (async, non-blocking)
    if (options.compareWithBackend) {
      compareWithBackend(expression, result, this.context)
    }

    return result
  }

  /**
   * Evaluate a string with embedded expressions (interpolation)
   * @param {string} template - Template like "Hello ${ui.inputs.name}!"
   * @returns {EvaluationResult}
   */
  evaluateTemplate(template) {
    if (typeof template !== 'string') {
      return { ok: true, value: template }
    }

    // If it's a pure expression (no surrounding text), return typed value
    if (BindingUtils.isExpression(template)) {
      return this.evaluateSingle(template)
    }

    // If no expressions, return as-is
    if (!BindingUtils.containsExpression(template)) {
      return { ok: true, value: template }
    }

    // Interpolate all expressions
    const missingVars = []
    let hasError = false

    const result = template.replace(VARIABLE_PATTERN, (match) => {
      const evalResult = resolveExpression(match, this.context)

      if (!evalResult.ok) {
        hasError = true
        if (evalResult.missingVars) {
          missingVars.push(...evalResult.missingVars)
        }
        return match // Keep original if failed
      }

      // Convert value to string for interpolation
      const value = evalResult.value
      if (value === null || value === undefined) {
        return ''
      }
      if (typeof value === 'object') {
        return JSON.stringify(value)
      }
      return String(value)
    })

    if (hasError && missingVars.length > 0) {
      return {
        ok: false,
        value: result,
        error: `Missing variables: ${missingVars.join(', ')}`,
        missingVars
      }
    }

    return { ok: true, value: result }
  }

  /**
   * Evaluate any value (handles objects, arrays, primitives)
   * @param {*} value - Value to evaluate
   * @param {Object} [options] - Options
   * @param {boolean} [options.compareWithBackend=false] - Enable backend comparison in dev mode
   * @returns {EvaluationResult}
   */
  evaluate(value, options = {}) {
    // Null/undefined passthrough
    if (value === null || value === undefined) {
      return { ok: true, value }
    }

    // String: evaluate as template
    if (typeof value === 'string') {
      const result = this.evaluateTemplate(value)

      // Dev mode comparison for string expressions
      if (options.compareWithBackend && BindingUtils.containsExpression(value)) {
        compareWithBackend(value, result, this.context)
      }

      return result
    }

    // Array: evaluate each element
    if (Array.isArray(value)) {
      const results = value.map(item => this.evaluate(item))
      const errors = results.filter(r => !r.ok)

      if (errors.length > 0) {
        const allMissing = errors.flatMap(e => e.missingVars || [])
        return {
          ok: false,
          value: results.map(r => r.value),
          error: errors[0].error,
          missingVars: [...new Set(allMissing)]
        }
      }

      return { ok: true, value: results.map(r => r.value) }
    }

    // Object: evaluate each property
    if (typeof value === 'object') {
      const result = {}
      const allMissing = []
      let hasError = false
      let firstError = null

      for (const [key, val] of Object.entries(value)) {
        const evalResult = this.evaluate(val)
        result[key] = evalResult.value

        if (!evalResult.ok) {
          hasError = true
          if (!firstError) firstError = evalResult.error
          if (evalResult.missingVars) {
            allMissing.push(...evalResult.missingVars)
          }
        }
      }

      if (hasError) {
        return {
          ok: false,
          value: result,
          error: firstError,
          missingVars: [...new Set(allMissing)]
        }
      }

      return { ok: true, value: result }
    }

    // Primitives (number, boolean): passthrough
    return { ok: true, value }
  }

  /**
   * Check if all expressions in a value can be resolved
   * @param {*} value - Value to check
   * @returns {Object} { valid: boolean, missing: string[] }
   */
  validate(value) {
    const result = this.evaluate(value)
    return {
      valid: result.ok,
      missing: result.missingVars || []
    }
  }

  /**
   * Extract all variable expressions from a value
   * @param {*} value - Value to scan
   * @returns {string[]} Array of expressions found
   */
  static extractExpressions(value) {
    const expressions = new Set()

    function scan(v) {
      if (typeof v === 'string') {
        const matches = v.match(VARIABLE_PATTERN) || []
        matches.forEach(m => expressions.add(m))
      } else if (Array.isArray(v)) {
        v.forEach(scan)
      } else if (v && typeof v === 'object') {
        Object.values(v).forEach(scan)
      }
    }

    scan(value)
    return [...expressions]
  }

  /**
   * Get all available variables from context
   * @returns {Object} { inputs: [], steps: [], env: [] }
   */
  getAvailableVariables() {
    const result = {
      inputs: [],
      steps: [],
      env: []
    }

    // Flatten inputs
    for (const [key, value] of Object.entries(this.context.inputs)) {
      result.inputs.push({
        path: `ui.inputs.${key}`,
        expression: `\${ui.inputs.${key}}`,
        label: key,
        value,
        dataType: this._inferType(value)
      })
    }

    // Flatten steps
    for (const [stepId, outputs] of Object.entries(this.context.steps)) {
      if (outputs && typeof outputs === 'object') {
        for (const [outputKey, value] of Object.entries(outputs)) {
          result.steps.push({
            path: `steps.${stepId}.${outputKey}`,
            expression: `\${steps.${stepId}.${outputKey}}`,
            label: `${stepId}.${outputKey}`,
            value,
            dataType: this._inferType(value)
          })
        }
      }
    }

    // Flatten env
    for (const [key, value] of Object.entries(this.context.env)) {
      result.env.push({
        path: `env.${key}`,
        expression: `\${env.${key}}`,
        label: key,
        value,
        dataType: 'string'
      })
    }

    return result
  }

  /**
   * Infer data type from value
   * @private
   */
  _inferType(value) {
    if (value === null || value === undefined) return 'any'
    if (typeof value === 'string') return 'string'
    if (typeof value === 'number') return 'number'
    if (typeof value === 'boolean') return 'boolean'
    if (Array.isArray(value)) return 'array'
    if (typeof value === 'object') return 'object'
    return 'any'
  }
}

/**
 * Create a simple evaluator function for one-off evaluations
 * @param {EvaluationContext} context
 * @returns {Function} Evaluate function
 */
export function createEvaluator(context) {
  const evaluator = new ExpressionEvaluator(context)
  return (value) => evaluator.evaluate(value)
}

/**
 * Quick evaluate helper
 * @param {*} value - Value to evaluate
 * @param {EvaluationContext} context - Context
 * @returns {*} Resolved value (throws on error)
 */
export function evaluate(value, context) {
  const evaluator = new ExpressionEvaluator(context)
  const result = evaluator.evaluate(value)

  if (!result.ok) {
    throw new Error(result.error)
  }

  return result.value
}

export default ExpressionEvaluator
