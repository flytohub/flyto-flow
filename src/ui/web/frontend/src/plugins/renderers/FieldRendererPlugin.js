/**
 * Field Renderer Plugin Base
 * Extend this for custom field type renderers
 */

import { PluginInterface } from '../core/PluginInterface'

export class FieldRendererPlugin extends PluginInterface {
  /**
   * Plugin category (fixed)
   * @type {string}
   */
  static get category() {
    return 'fieldRenderer'
  }

  /**
   * Field type this plugin handles
   * @type {string}
   */
  static get fieldType() {
    throw new Error('FieldRendererPlugin must define fieldType')
  }

  /**
   * Alias for pluginId (uses fieldType)
   * @type {string}
   */
  static get pluginId() {
    return this.fieldType
  }

  /**
   * Vue component for rendering
   * @type {Object}
   */
  static get component() {
    throw new Error('FieldRendererPlugin must provide component')
  }

  /**
   * Data type this field produces
   * @type {string}
   */
  static get dataType() {
    return 'string'
  }

  /**
   * HTML input type (for input fields)
   * @type {string}
   */
  static get inputType() {
    return 'text'
  }

  /**
   * Whether field supports direct editing
   * @type {boolean}
   */
  static get supportsDirectEdit() {
    return false
  }

  /**
   * Default props for this field type
   * @type {Object}
   */
  static get defaultProps() {
    return {
      placeholder: '',
      disabled: false,
      required: false,
    }
  }

  /**
   * Icon for this field type (lucide icon name)
   * @type {string}
   */
  static get icon() {
    return 'Type'
  }

  /**
   * Get default value for this field type
   * @returns {any}
   */
  static getDefaultValue() {
    switch (this.dataType) {
      case 'boolean':
        return false
      case 'number':
        return 0
      case 'array':
        return []
      case 'object':
        return {}
      default:
        return ''
    }
  }

  /**
   * Validate field value
   * @param {any} value - Value to validate
   * @param {Object} config - Field configuration
   * @returns {{ valid: boolean, errors: string[] }}
   */
  static validateValue(value, config = {}) {
    const errors = []

    if (config.required && (value === undefined || value === null || value === '')) {
      errors.push('This field is required')
    }

    return { valid: errors.length === 0, errors }
  }
}

/**
 * Create a simple field renderer plugin
 * @param {Object} config - Plugin configuration
 * @returns {Object} Plugin object
 */
export function createFieldPlugin(config) {
  return {
    pluginId: config.type,
    fieldType: config.type,
    component: config.component,
    dataType: config.dataType || 'string',
    inputType: config.inputType || 'text',
    supportsDirectEdit: config.supportsDirectEdit || false,
    defaultProps: config.defaultProps || {},
    icon: config.icon || 'Type',
    getDefaultValue: config.getDefaultValue || FieldRendererPlugin.getDefaultValue,
    validateValue: config.validateValue || FieldRendererPlugin.validateValue,
  }
}
