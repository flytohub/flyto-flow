/**
 * Connection Validation Rules (UX HINTS ONLY)
 *
 * S-Grade: Validate node connections for immediate user feedback.
 * Single responsibility: Connection validation logic.
 *
 * IMPORTANT: These validations are UX hints only, NOT authoritative.
 * The authoritative validation is done by the backend via POST /workflows/validate.
 * Frontend validation provides instant feedback but can be bypassed.
 * Always call backend validation before save/execute.
 */

import { hasReachedMaxOutputs } from './branchRules'

/**
 * Validate if a connection between two nodes is allowed (UX HINT)
 *
 * Note: This is for immediate visual feedback only.
 * Authoritative validation happens server-side via POST /api/workflows/validate.
 *
 * @param {Object} params
 * @param {string} params.sourceId
 * @param {string} params.targetId
 * @param {Array} params.nodes
 * @param {Array} params.edges
 * @returns {Object} { valid: boolean, reason?: string, isHint: true }
 */
export function validateConnection({ sourceId, targetId, nodes, edges }) {
  // Rule: No self-connections
  if (sourceId === targetId) {
    return { valid: false, reason: 'Cannot connect node to itself', isHint: true }
  }

  // Rule: No duplicate connections
  const exists = edges.some(
    e => e.source === sourceId && e.target === targetId
  )
  if (exists) {
    return { valid: false, reason: 'Connection already exists', isHint: true }
  }

  // Rule: Check max outputs
  const sourceNode = nodes.find(n => n.id === sourceId)
  if (sourceNode && hasReachedMaxOutputs(sourceId, edges, sourceNode)) {
    return { valid: false, reason: 'Node has reached maximum outputs', isHint: true }
  }

  // Rule: Prevent cycles (unless loop mode) - simplified check
  // Full cycle detection is done server-side

  return { valid: true, isHint: true }
}
