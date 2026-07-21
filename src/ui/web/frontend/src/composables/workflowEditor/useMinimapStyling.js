/**
 * Minimap Styling Composable
 *
 * Extracted from WorkflowCanvas.vue to reduce component size.
 * Provides styling functions for VueFlow MiniMap component.
 *
 * Color scheme:
 * - Cyan (#22D3EE): Triggers, webhooks, schedules, start
 * - Yellow (#FBBF24): Branch/if nodes
 * - Orange (#F97316): Switch/case nodes
 * - Green (#34D399): Loop/forEach nodes
 * - Red (#F87171): Error handlers
 * - Blue (#60A5FA): HTTP/API nodes
 * - Violet (#A78BFA): Code/script nodes
 * - Purple (#C084FC): Default
 *
 * @module useMinimapStyling
 */

/**
 * Module type patterns for color mapping
 */
const MODULE_PATTERNS = {
  trigger: ['trigger', 'webhook', 'schedule', 'flow.start'],
  branch: ['branch', 'if'],
  switch: ['switch', 'case'],
  loop: ['loop', 'foreach', 'repeat', 'while', 'for.each', 'flow.loop'],
  error: ['error', 'catch', 'try'],
  http: ['http', 'api', 'fetch', 'request'],
  code: ['code', 'script', 'javascript', 'python']
}

/**
 * Color palette for minimap nodes
 */
const COLORS = {
  trigger: { fill: '#22D3EE', stroke: '#06B6D4' },
  branch: { fill: '#FBBF24', stroke: '#F59E0B' },
  switch: { fill: '#F97316', stroke: '#EA580C' },
  loop: { fill: '#34D399', stroke: '#10B981' },
  error: { fill: '#F87171', stroke: '#EF4444' },
  http: { fill: '#60A5FA', stroke: '#3B82F6' },
  code: { fill: '#A78BFA', stroke: '#8B5CF6' },
  default: { fill: '#C084FC', stroke: '#A855F7' }
}

/**
 * Detect module type from module ID
 */
function detectModuleType(moduleId) {
  if (!moduleId) return 'default'

  for (const [type, patterns] of Object.entries(MODULE_PATTERNS)) {
    if (patterns.some(p => moduleId.includes(p))) {
      return type
    }
  }

  return 'default'
}

/**
 * Create minimap styling composable
 *
 * @returns {Object} Minimap styling functions
 */
export function useMinimapStyling() {
  /**
   * Get fill color for a minimap node
   *
   * @param {Object} node - VueFlow node
   * @returns {string} Hex color
   */
  function getMinimapNodeColor(node) {
    const moduleId = node.data?.module || ''
    const type = detectModuleType(moduleId)
    return COLORS[type].fill
  }

  /**
   * Get stroke color for a minimap node
   *
   * @param {Object} node - VueFlow node
   * @returns {string} Hex color
   */
  function getMinimapNodeStroke(node) {
    const moduleId = node.data?.module || ''
    const type = detectModuleType(moduleId)
    return COLORS[type].stroke
  }

  /**
   * Get CSS class for a minimap node
   *
   * @param {Object} node - VueFlow node
   * @returns {string} CSS class name(s)
   */
  function getMinimapNodeClass(node) {
    const moduleId = node.data?.module || ''
    const classes = ['minimap-node']
    const type = detectModuleType(moduleId)

    if (type !== 'default') {
      classes.push(`minimap-${type}`)
    }

    // Add selected class
    if (node.selected) {
      classes.push('minimap-selected')
    }

    return classes.join(' ')
  }

  /**
   * Get all colors for custom theming
   */
  function getColors() {
    return { ...COLORS }
  }

  /**
   * Update colors for custom theming
   *
   * @param {Object} customColors - Custom color overrides
   */
  function setCustomColors(customColors) {
    Object.assign(COLORS, customColors)
  }

  return {
    getMinimapNodeColor,
    getMinimapNodeStroke,
    getMinimapNodeClass,
    getColors,
    setCustomColors
  }
}

export default useMinimapStyling
