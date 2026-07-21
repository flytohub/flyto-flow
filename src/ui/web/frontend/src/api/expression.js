/**
 * Expression API Client
 *
 * Client for backend expression evaluation endpoints.
 * The backend provides secure AST-based expression evaluation.
 *
 * Use these endpoints for:
 * - Authoritative expression evaluation (workflow execution)
 * - Syntax validation before save
 * - Batch parameter evaluation
 *
 * Note: For UI preview, the local ExpressionEvaluator can be used for
 * instant feedback. But for actual workflow execution, always use
 * backend evaluation.
 */

import { post, get } from './client'
import { ENDPOINTS } from './config'

export const expressionAPI = {
  /**
   * Evaluate a single expression
   * @param {string} expression - Expression to evaluate
   * @param {Object} context - Variable context
   * @param {string} type - Expression type: 'condition', 'arithmetic', 'interpolate', 'auto'
   * @returns {Promise<{ok: boolean, result: any, error?: string}>}
   */
  async evaluate(expression, context = {}, type = 'auto') {
    return post('/expression/evaluate', { expression, context, type })
  },

  /**
   * Validate expression syntax
   * @param {string} expression - Expression to validate
   * @returns {Promise<{ok: boolean, valid: boolean, variables: string[], warnings: string[]}>}
   */
  async validate(expression) {
    return post('/expression/validate', { expression })
  },

  /**
   * Evaluate multiple expressions with shared context
   * @param {Object<string, string>} expressions - Map of key -> expression
   * @param {Object} context - Shared variable context
   * @returns {Promise<{ok: boolean, results: Object, errors: Object}>}
   */
  async batch(expressions, context = {}) {
    return post('/expression/batch', { expressions, context })
  },

  /**
   * Get list of allowed functions in expressions
   * @returns {Promise<{ok: boolean, allowedFunctions: string[]}>}
   */
  async getAllowedFunctions() {
    return get('/expression/functions')
  }
}

export default expressionAPI
