/**
 * ID Generators
 *
 * S-Grade: ID generation utilities.
 * Single responsibility: Generate unique identifiers.
 */

import { EDGE_PREFIXES } from './edgeConstants'

/**
 * Generate a unique random suffix for IDs
 * @returns {string} 6-character random string
 */
export function getRandomSuffix() {
  return Math.random().toString(36).substring(2, 8)
}

/**
 * Generate a unique node ID
 * @param {string} prefix - Optional prefix for the ID
 * @returns {string}
 */
export function generateNodeId(prefix = 'node') {
  return `${prefix}_${Date.now()}_${getRandomSuffix()}`
}

/**
 * Generate a unique edge ID
 * @param {string} sourceId - Source node ID
 * @param {string} targetId - Target node ID
 * @param {boolean} isLoop - Whether this is a loop edge
 * @returns {string}
 */
export function generateEdgeId(sourceId, targetId, isLoop = false) {
  const prefix = isLoop ? EDGE_PREFIXES.LOOP : EDGE_PREFIXES.NORMAL
  return `${prefix}${sourceId}_${targetId}_${getRandomSuffix()}`
}
