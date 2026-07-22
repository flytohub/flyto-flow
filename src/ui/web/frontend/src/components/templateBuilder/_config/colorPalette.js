/**
 * Color Palette
 *
 * Centralized color definitions for the template builder.
 * All colors should be referenced from here, not hardcoded.
 */

// Component type colors
export const COMPONENT_COLORS = {
  input: '#3B82F6',
  number: '#3B82F6',
  email: '#3B82F6',
  password: '#3B82F6',
  url: '#3B82F6',
  tel: '#3B82F6',
  textarea: '#06B6D4',
  select: '#8B5CF6',
  checkbox: '#10B981',
  radio: '#F59E0B',
  switch: '#10B981',
  date: '#F97316',
  time: '#F97316',
  range: '#EC4899',
  rating: '#EAB308',
  file: '#6366F1',
  color: '#EC4899',
  datetime: '#F97316',
  path: '#6366F1',
  array: '#14B8A6',
  keyvalue: '#14B8A6',
  json: '#06B6D4',
  heading: '#64748B',
  text: '#64748B',
  divider: '#64748B',
  image: '#14B8A6',
  button: '#EC4899'
}

// UI state colors
export const STATE_COLORS = {
  selected: '#8B5CF6',
  hover: '#A78BFA',
  active: '#7C3AED',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6'
}

// Background colors
export const BG_COLORS = {
  primary: '#0f172a',
  secondary: '#1e293b',
  tertiary: '#334155',
  card: 'rgba(30, 41, 59, 0.5)',
  input: 'rgba(15, 23, 42, 0.6)',
  overlay: 'rgba(0, 0, 0, 0.3)'
}

// Border colors
export const BORDER_COLORS = {
  default: '#334155',
  hover: '#475569',
  focus: '#8B5CF6',
  selected: '#8B5CF6'
}

// Text colors
export const TEXT_COLORS = {
  primary: '#f1f5f9',
  secondary: '#94a3b8',
  muted: '#64748b',
  placeholder: '#64748b'
}

// Fallback color for unknown component types
export const FALLBACK_COLOR = '#6B7280'

/**
 * Get color for component type
 * @param {string} type - Component type
 * @returns {string} Color hex value
 */
export function getComponentColor(type) {
  return COMPONENT_COLORS[type] || FALLBACK_COLOR
}

/**
 * Get CSS custom properties for a component
 * @param {string} type - Component type
 * @returns {Object} CSS variables object
 */
export function getComponentCSSVars(type) {
  const color = getComponentColor(type)
  return {
    '--comp-color': color,
    '--comp-bg': `color-mix(in srgb, ${color} 15%, transparent)`,
    '--comp-border': `color-mix(in srgb, ${color} 30%, transparent)`
  }
}

export default {
  COMPONENT_COLORS,
  STATE_COLORS,
  BG_COLORS,
  BORDER_COLORS,
  TEXT_COLORS,
  FALLBACK_COLOR,
  getComponentColor,
  getComponentCSSVars
}
