/**
 * Port Types Constants
 *
 * Workflow Spec v1.1 - Port type definitions
 * Single source of truth for port-related constants
 */

// Node types from Workflow Spec v1.1
export const NODE_TYPES = Object.freeze({
  STANDARD: 'standard',
  BRANCH: 'branch',
  SWITCH: 'switch',
  LOOP: 'loop',
  MERGE: 'merge',
  FORK: 'fork',
  JOIN: 'join',
  CONTAINER: 'container',
  SUBFLOW: 'subflow',
  TRIGGER: 'trigger',
  START: 'start',
  END: 'end'
})

// Edge types
export const EDGE_TYPES = Object.freeze({
  CONTROL: 'control',
  RESOURCE: 'resource'
})

// Data types for port validation
export const DATA_TYPES = Object.freeze({
  ANY: 'any',
  STRING: 'string',
  NUMBER: 'number',
  BOOLEAN: 'boolean',
  OBJECT: 'object',
  ARRAY: 'array',
  BINARY: 'binary',
  TABLE: 'table',
  BROWSER: 'browser',
  PAGE: 'page',
  ELEMENT: 'element',
  FILE: 'file',
  IMAGE: 'image',
  JSON: 'json',
  XML: 'xml',
  HTML: 'html',
  CREDENTIAL: 'credential'
})

// Port importance levels (UI visibility)
export const PORT_IMPORTANCE = Object.freeze({
  PRIMARY: 'primary',
  SECONDARY: 'secondary',
  ADVANCED: 'advanced'
})

// Port positions
export const PORT_POSITIONS = Object.freeze({
  LEFT: 'left',
  RIGHT: 'right',
  TOP: 'top',
  BOTTOM: 'bottom'
})

// Default port colors
export const PORT_COLORS = Object.freeze({
  SUCCESS: '#10B981',
  ERROR: '#EF4444',
  DEFAULT: '#6B7280',
  TRUE: '#10B981',
  FALSE: '#F59E0B',
  ITEM: '#3B82F6',
  DONE: '#10B981',
  TIMEOUT: '#F59E0B',
  CONTROL: '#8B5CF6',
  RESOURCE: '#06B6D4'
})

// Type compatibility matrix
export const TYPE_COMPATIBILITY = Object.freeze({
  [DATA_TYPES.ANY]: Object.values(DATA_TYPES),
  [DATA_TYPES.STRING]: [DATA_TYPES.ANY, DATA_TYPES.STRING, DATA_TYPES.JSON, DATA_TYPES.XML, DATA_TYPES.HTML],
  [DATA_TYPES.NUMBER]: [DATA_TYPES.ANY, DATA_TYPES.NUMBER, DATA_TYPES.STRING],
  [DATA_TYPES.BOOLEAN]: [DATA_TYPES.ANY, DATA_TYPES.BOOLEAN, DATA_TYPES.STRING, DATA_TYPES.NUMBER],
  [DATA_TYPES.OBJECT]: [DATA_TYPES.ANY, DATA_TYPES.OBJECT, DATA_TYPES.JSON],
  [DATA_TYPES.ARRAY]: [DATA_TYPES.ANY, DATA_TYPES.ARRAY, DATA_TYPES.TABLE],
  [DATA_TYPES.JSON]: [DATA_TYPES.ANY, DATA_TYPES.JSON, DATA_TYPES.OBJECT, DATA_TYPES.STRING],
  [DATA_TYPES.TABLE]: [DATA_TYPES.ANY, DATA_TYPES.TABLE, DATA_TYPES.ARRAY],
  [DATA_TYPES.BROWSER]: [DATA_TYPES.ANY, DATA_TYPES.BROWSER],
  [DATA_TYPES.PAGE]: [DATA_TYPES.ANY, DATA_TYPES.PAGE, DATA_TYPES.BROWSER],
  [DATA_TYPES.ELEMENT]: [DATA_TYPES.ANY, DATA_TYPES.ELEMENT],
  [DATA_TYPES.FILE]: [DATA_TYPES.ANY, DATA_TYPES.FILE, DATA_TYPES.BINARY],
  [DATA_TYPES.IMAGE]: [DATA_TYPES.ANY, DATA_TYPES.IMAGE, DATA_TYPES.FILE, DATA_TYPES.BINARY],
  [DATA_TYPES.BINARY]: [DATA_TYPES.ANY, DATA_TYPES.BINARY],
  [DATA_TYPES.XML]: [DATA_TYPES.ANY, DATA_TYPES.XML, DATA_TYPES.STRING],
  [DATA_TYPES.HTML]: [DATA_TYPES.ANY, DATA_TYPES.HTML, DATA_TYPES.STRING],
  [DATA_TYPES.CREDENTIAL]: [DATA_TYPES.ANY, DATA_TYPES.CREDENTIAL]
})

// Default ports by node type
export const DEFAULT_PORTS = Object.freeze({
  [NODE_TYPES.STANDARD]: {
    input: [{ id: 'input', label: 'Input', maxConnections: 1, required: true }],
    output: [
      { id: 'success', label: 'Success', event: 'success', color: PORT_COLORS.SUCCESS },
      { id: 'error', label: 'Error', event: 'error', color: PORT_COLORS.ERROR }
    ]
  },
  [NODE_TYPES.BRANCH]: {
    input: [{ id: 'input', label: 'Input', maxConnections: 1, required: true }],
    output: [
      { id: 'true', label: 'True', event: 'true', color: PORT_COLORS.TRUE },
      { id: 'false', label: 'False', event: 'false', color: PORT_COLORS.FALSE },
      { id: 'error', label: 'Error', event: 'error', color: PORT_COLORS.ERROR }
    ]
  },
  [NODE_TYPES.SWITCH]: {
    input: [{ id: 'input', label: 'Input', maxConnections: 1, required: true }],
    output: [
      { id: 'default', label: 'Default', event: 'default', color: PORT_COLORS.DEFAULT },
      { id: 'error', label: 'Error', event: 'error', color: PORT_COLORS.ERROR }
    ]
  },
  [NODE_TYPES.LOOP]: {
    input: [{ id: 'input', label: 'Input', maxConnections: 1, required: true }],
    output: [
      { id: 'item', label: 'Each Item', event: 'item', color: PORT_COLORS.ITEM },
      { id: 'done', label: 'Done', event: 'done', color: PORT_COLORS.DONE },
      { id: 'error', label: 'Error', event: 'error', color: PORT_COLORS.ERROR }
    ]
  },
  [NODE_TYPES.MERGE]: {
    input: [{ id: 'input', label: 'Input', maxConnections: null }],
    output: [{ id: 'output', label: 'Output', event: 'success' }]
  },
  [NODE_TYPES.JOIN]: {
    input: [{ id: 'input', label: 'Input', maxConnections: null }],
    output: [
      { id: 'output', label: 'Output', event: 'success' },
      { id: 'timeout', label: 'Timeout', event: 'timeout', color: PORT_COLORS.TIMEOUT },
      { id: 'error', label: 'Error', event: 'error', color: PORT_COLORS.ERROR }
    ]
  },
  [NODE_TYPES.TRIGGER]: {
    input: [],
    output: [{ id: 'trigger', label: 'Trigger', event: 'trigger' }]
  },
  [NODE_TYPES.START]: {
    input: [],
    output: [{ id: 'start', label: 'Start', event: 'start' }]
  },
  [NODE_TYPES.END]: {
    input: [{ id: 'input', label: 'Input', maxConnections: null }],
    output: []
  }
})
