/**
 * Field Renderer Plugins Registration
 * Registers all field renderers with the plugin system
 */

import { PluginRegistry } from '@/plugins/core/PluginRegistry'
import { RendererResolver } from '@/plugins/core/RendererResolver'
import { createFieldPlugin } from '@/plugins/renderers/FieldRendererPlugin'

// Import all renderer components
import TextFieldRenderer from './TextFieldRenderer.vue'
import TextareaRenderer from './TextareaRenderer.vue'
import SelectRenderer from './SelectRenderer.vue'
import CheckboxRenderer from './CheckboxRenderer.vue'
import SwitchRenderer from './SwitchRenderer.vue'
import RadioRenderer from './RadioRenderer.vue'
import RangeRenderer from './RangeRenderer.vue'
import RatingRenderer from './RatingRenderer.vue'
import FileRenderer from './FileRenderer.vue'
import DateRenderer from './DateRenderer.vue'
import TimeRenderer from './TimeRenderer.vue'
import ColorRenderer from './ColorRenderer.vue'
import FallbackRenderer from './FallbackRenderer.vue'

// Define field type configurations
const FIELD_PLUGINS = [
  // Text-based inputs
  { type: 'text', component: TextFieldRenderer, dataType: 'string', inputType: 'text' },
  { type: 'input', component: TextFieldRenderer, dataType: 'string', inputType: 'text' },
  { type: 'email', component: TextFieldRenderer, dataType: 'string', inputType: 'email' },
  { type: 'password', component: TextFieldRenderer, dataType: 'string', inputType: 'password' },
  { type: 'url', component: TextFieldRenderer, dataType: 'string', inputType: 'url' },
  { type: 'tel', component: TextFieldRenderer, dataType: 'string', inputType: 'tel' },
  { type: 'number', component: TextFieldRenderer, dataType: 'number', inputType: 'number' },

  // Textarea
  { type: 'textarea', component: TextareaRenderer, dataType: 'string' },

  // Select/Options
  { type: 'select', component: SelectRenderer, dataType: 'string' },
  { type: 'radio', component: RadioRenderer, dataType: 'string' },

  // Boolean
  { type: 'checkbox', component: CheckboxRenderer, dataType: 'boolean' },
  { type: 'switch', component: SwitchRenderer, dataType: 'boolean' },

  // Numeric
  { type: 'range', component: RangeRenderer, dataType: 'number' },
  { type: 'rating', component: RatingRenderer, dataType: 'number' },

  // File
  { type: 'file', component: FileRenderer, dataType: 'file' },
  { type: 'image', component: FileRenderer, dataType: 'file' },

  // Date/Time
  { type: 'date', component: DateRenderer, dataType: 'string' },
  { type: 'time', component: TimeRenderer, dataType: 'string' },

  // Color
  { type: 'color', component: ColorRenderer, dataType: 'string' },
]

/**
 * Register all field renderer plugins
 */
export function registerFieldRenderers() {
  FIELD_PLUGINS.forEach(config => {
    const plugin = createFieldPlugin(config)
    PluginRegistry.register(plugin, 'fieldRenderer')
  })

  // Set fallback renderer
  RendererResolver.setFallback('fieldRenderer', FallbackRenderer)

}

/**
 * Get default value for a field type
 * @param {string} type - Field type
 * @returns {any}
 */
export function getDefaultValue(type) {
  const plugin = PluginRegistry.get(type, 'fieldRenderer')
  if (plugin?.dataType === 'boolean') return false
  if (plugin?.dataType === 'number') return 0
  if (plugin?.dataType === 'array') return []
  return ''
}

/**
 * Check if a type is a text input
 * @param {string} type - Field type
 * @returns {boolean}
 */
export function isTextInput(type) {
  return ['text', 'input', 'email', 'password', 'url', 'tel', 'number'].includes(type)
}

// Export components for direct use
export {
  TextFieldRenderer,
  TextareaRenderer,
  SelectRenderer,
  CheckboxRenderer,
  SwitchRenderer,
  RadioRenderer,
  RangeRenderer,
  RatingRenderer,
  FileRenderer,
  DateRenderer,
  TimeRenderer,
  ColorRenderer,
  FallbackRenderer,
}
