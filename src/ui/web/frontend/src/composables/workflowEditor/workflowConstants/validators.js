/**
 * Element Validators
 *
 * S-Grade: Element validation utilities.
 * Single responsibility: Validate workflow elements.
 */

/**
 * Validate that elements array is properly formatted
 * @param {Array} elements - Elements to validate
 * @returns {{ valid: boolean, errors: string[] }}
 */
export function validateElements(elements) {
  const errors = []

  if (!elements) {
    errors.push('Elements is null or undefined')
    return { valid: false, errors }
  }

  if (!Array.isArray(elements)) {
    errors.push('Elements is not an array')
    return { valid: false, errors }
  }

  // Check for malformed nodes
  const nodes = elements.filter(el => el.id && !el.source && !el.target)
  const edges = elements.filter(el => el.source && el.target)

  nodes.forEach((node, i) => {
    if (!node.id) {
      errors.push(`Node at index ${i} has no ID`)
    }
    if (!node.position) {
      errors.push(`Node ${node.id || i} has no position`)
    }
  })

  edges.forEach((edge, i) => {
    if (!edge.source || typeof edge.source !== 'string') {
      errors.push(`Edge at index ${i} has invalid source`)
    }
    if (!edge.target || typeof edge.target !== 'string') {
      errors.push(`Edge at index ${i} has invalid target`)
    }
  })

  return { valid: errors.length === 0, errors }
}

/**
 * Separate elements into nodes and edges with validation
 * @param {Array} elements - Elements array
 * @returns {{ nodes: Array, edges: Array }}
 */
export function separateElements(elements) {
  if (!elements || !Array.isArray(elements)) {
    return { nodes: [], edges: [] }
  }

  const nodes = elements.filter(el =>
    el && el.id && !el.source && !el.target
  )

  const edges = elements.filter(el =>
    el && typeof el.source === 'string' && typeof el.target === 'string'
  )

  return { nodes, edges }
}
