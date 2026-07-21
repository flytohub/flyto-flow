/**
 * Prompt Template Utilities
 *
 * Utilities for working with prompt templates that support
 * variable interpolation using {{variable}} syntax.
 */

/**
 * Extract variable names from a prompt template
 * @param {string} template - The template string with {{variables}}
 * @returns {string[]} Array of variable names found in template
 *
 * @example
 * extractVariables('Hello {{name}}, your score is {{score}}')
 * // Returns: ['name', 'score']
 */
export function extractVariables(template) {
  if (!template || typeof template !== 'string') return []

  const regex = /\{\{([^}]+)\}\}/g
  const variables = []
  let match

  while ((match = regex.exec(template)) !== null) {
    const varName = match[1].trim()
    if (varName && !variables.includes(varName)) {
      variables.push(varName)
    }
  }

  return variables
}

export default {
  extractVariables
}
