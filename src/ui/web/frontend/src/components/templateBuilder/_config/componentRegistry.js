/**
 * Component Registry
 *
 * Central configuration for all UI components available in the template builder.
 * This replaces hardcoded component lists throughout the codebase.
 *
 * Each component type defines:
 * - type: Unique identifier
 * - label: Display name (i18n key)
 * - icon: Lucide icon name
 * - category: Category key for filtering
 * - color: Theme color
 * - defaultProps: Default property values
 * - previewComponent: Component name for live preview
 * - supportsDirectEdit: Whether clicking preview allows editing
 */

export const COMPONENT_TYPES = {
  // Basic Input
  input: {
    type: 'input',
    labelKey: 'component.textInput',
    icon: 'TextCursorInput',
    category: 'basic-input',
    color: '#3B82F6',
    defaultProps: {
      inputType: 'text',
      placeholder: '',
      default: ''
    },
    previewComponent: 'InputPreview',
    supportsDirectEdit: true
  },

  number: {
    type: 'number',
    labelKey: 'component.numberInput',
    icon: 'Hash',
    category: 'basic-input',
    color: '#3B82F6',
    defaultProps: {
      placeholder: '',
      default: 0,
      min: null,
      max: null,
      step: 1
    },
    previewComponent: 'NumberPreview',
    supportsDirectEdit: true
  },

  email: {
    type: 'email',
    labelKey: 'component.emailInput',
    icon: 'Mail',
    category: 'basic-input',
    color: '#3B82F6',
    defaultProps: {
      placeholder: '',
      default: ''
    },
    previewComponent: 'EmailPreview',
    supportsDirectEdit: true
  },

  password: {
    type: 'password',
    labelKey: 'component.passwordInput',
    icon: 'Lock',
    category: 'basic-input',
    color: '#3B82F6',
    defaultProps: {
      placeholder: '',
      default: ''
    },
    previewComponent: 'PasswordPreview',
    supportsDirectEdit: true
  },

  url: {
    type: 'url',
    labelKey: 'component.urlInput',
    icon: 'Link',
    category: 'basic-input',
    color: '#3B82F6',
    defaultProps: {
      placeholder: '',
      default: ''
    },
    previewComponent: 'UrlPreview',
    supportsDirectEdit: true
  },

  tel: {
    type: 'tel',
    labelKey: 'templateBuilder.properties.inputTypeTel',
    icon: 'Phone',
    category: 'basic-input',
    color: '#3B82F6',
    defaultProps: {
      placeholder: '',
      default: ''
    },
    previewComponent: 'TelPreview',
    supportsDirectEdit: true
  },

  textarea: {
    type: 'textarea',
    labelKey: 'component.textarea',
    icon: 'FileType',
    category: 'basic-input',
    color: '#06B6D4',
    defaultProps: {
      rows: 4,
      placeholder: '',
      default: ''
    },
    previewComponent: 'TextareaPreview',
    supportsDirectEdit: true
  },

  // Selectors
  select: {
    type: 'select',
    labelKey: 'component.select',
    icon: 'ChevronDown',
    category: 'selectors',
    color: '#8B5CF6',
    defaultProps: {
      options: [],
      default: '',
      multiple: false,
      searchable: false
    },
    previewComponent: 'SelectPreview',
    supportsDirectEdit: true
  },

  checkbox: {
    type: 'checkbox',
    labelKey: 'component.checkbox',
    icon: 'SquareCheck',
    category: 'selectors',
    color: '#10B981',
    defaultProps: {
      default: false
    },
    previewComponent: 'CheckboxPreview',
    supportsDirectEdit: true
  },

  radio: {
    type: 'radio',
    labelKey: 'component.radio',
    icon: 'CircleDot',
    category: 'selectors',
    color: '#F59E0B',
    defaultProps: {
      options: [
        { value: 'yes', label: 'Yes' },
        { value: 'no', label: 'No' }
      ],
      default: '',
      layout: 'vertical'
    },
    previewComponent: 'RadioPreview',
    supportsDirectEdit: true
  },

  switch: {
    type: 'switch',
    labelKey: 'component.switch',
    icon: 'ToggleLeft',
    category: 'selectors',
    color: '#10B981',
    defaultProps: {
      default: false
    },
    previewComponent: 'SwitchPreview',
    supportsDirectEdit: true
  },

  // Date & Time
  date: {
    type: 'date',
    labelKey: 'component.date',
    icon: 'Calendar',
    category: 'datetime',
    color: '#F97316',
    defaultProps: {
      default: '',
      min: null,
      max: null
    },
    previewComponent: 'DatePreview',
    supportsDirectEdit: true
  },

  time: {
    type: 'time',
    labelKey: 'component.time',
    icon: 'Clock',
    category: 'datetime',
    color: '#F97316',
    defaultProps: {
      default: ''
    },
    previewComponent: 'TimePreview',
    supportsDirectEdit: true
  },

  // Date & Time (continued)
  datetime: {
    type: 'datetime',
    labelKey: 'component.datetime',
    icon: 'CalendarClock',
    category: 'datetime',
    color: '#F97316',
    defaultProps: {
      default: '',
      min: null,
      max: null
    },
    previewComponent: 'DatetimePreview',
    supportsDirectEdit: true
  },

  // Advanced Input
  color: {
    type: 'color',
    labelKey: 'component.colorPicker',
    icon: 'Palette',
    category: 'advanced-input',
    color: '#EC4899',
    defaultProps: {
      default: '#000000'
    },
    previewComponent: 'ColorPreview',
    supportsDirectEdit: true
  },

  path: {
    type: 'path',
    labelKey: 'component.pathInput',
    icon: 'FolderOpen',
    category: 'advanced-input',
    color: '#6366F1',
    defaultProps: {
      placeholder: '/path/to/file',
      default: ''
    },
    previewComponent: 'PathPreview',
    supportsDirectEdit: true
  },

  array: {
    type: 'array',
    labelKey: 'component.tagInput',
    icon: 'Tags',
    category: 'advanced-input',
    color: '#14B8A6',
    defaultProps: {
      default: [],
      placeholder: ''
    },
    previewComponent: 'ArrayPreview',
    supportsDirectEdit: true
  },

  keyvalue: {
    type: 'keyvalue',
    labelKey: 'component.keyValue',
    icon: 'Rows3',
    category: 'advanced-input',
    color: '#14B8A6',
    defaultProps: {
      default: {}
    },
    previewComponent: 'KeyValuePreview',
    supportsDirectEdit: false
  },

  json: {
    type: 'json',
    labelKey: 'component.jsonEditor',
    icon: 'Braces',
    category: 'advanced-input',
    color: '#06B6D4',
    defaultProps: {
      rows: 4,
      default: ''
    },
    previewComponent: 'JsonPreview',
    supportsDirectEdit: true
  },

  range: {
    type: 'range',
    labelKey: 'component.slider',
    icon: 'Sliders',
    category: 'advanced-input',
    color: '#EC4899',
    defaultProps: {
      min: 0,
      max: 100,
      step: 1,
      default: 50
    },
    previewComponent: 'RangePreview',
    supportsDirectEdit: true
  },

  rating: {
    type: 'rating',
    labelKey: 'component.rating',
    icon: 'Star',
    category: 'advanced-input',
    color: '#EAB308',
    defaultProps: {
      max: 5,
      default: 0
    },
    previewComponent: 'RatingPreview',
    supportsDirectEdit: true
  },

  file: {
    type: 'file',
    labelKey: 'component.fileUpload',
    icon: 'Upload',
    category: 'advanced-input',
    color: '#6366F1',
    defaultProps: {
      accept: '',
      multiple: false
    },
    previewComponent: 'FilePreview',
    supportsDirectEdit: false
  },

  // Display
  heading: {
    type: 'heading',
    labelKey: 'component.heading',
    icon: 'Heading1',
    category: 'display',
    color: '#64748B',
    defaultProps: {
      text: 'Heading',
      level: 'h2'
    },
    previewComponent: 'HeadingPreview',
    supportsDirectEdit: true
  },

  text: {
    type: 'text',
    labelKey: 'component.text',
    icon: 'AlignLeft',
    category: 'display',
    color: '#64748B',
    defaultProps: {
      text: 'Text content'
    },
    previewComponent: 'TextPreview',
    supportsDirectEdit: true
  },

  divider: {
    type: 'divider',
    labelKey: 'component.divider',
    icon: 'Minus',
    category: 'display',
    color: '#64748B',
    defaultProps: {},
    previewComponent: 'DividerPreview',
    supportsDirectEdit: false
  },

  image: {
    type: 'image',
    labelKey: 'component.image',
    icon: 'Image',
    category: 'display',
    color: '#14B8A6',
    defaultProps: {
      src: '',
      alt: '',
      width: 'auto',
      height: 'auto'
    },
    previewComponent: 'ImagePreview',
    supportsDirectEdit: false
  },

  // Buttons
  button: {
    type: 'button',
    labelKey: 'component.button',
    icon: 'RectangleHorizontal',
    category: 'buttons',
    color: '#EC4899',
    defaultProps: {
      text: 'Submit',
      buttonType: 'submit',
      variant: 'primary'
    },
    previewComponent: 'ButtonPreview',
    supportsDirectEdit: true
  }
}

/**
 * Component categories with display order
 */
export const COMPONENT_CATEGORIES = {
  'basic-input': {
    key: 'basic-input',
    labelKey: 'templateBuilder.categories.basicInput',
    order: 1
  },
  'selectors': {
    key: 'selectors',
    labelKey: 'templateBuilder.categories.selectors',
    order: 2
  },
  'datetime': {
    key: 'datetime',
    labelKey: 'templateBuilder.categories.dateTime',
    order: 3
  },
  'advanced-input': {
    key: 'advanced-input',
    labelKey: 'templateBuilder.categories.advancedInput',
    order: 4
  },
  'display': {
    key: 'display',
    labelKey: 'templateBuilder.categories.display',
    order: 5
  },
  'buttons': {
    key: 'buttons',
    labelKey: 'templateBuilder.categories.buttons',
    order: 6
  }
}

/**
 * Get component config by type
 * @param {string} type - Component type
 * @returns {Object|null} Component configuration
 */
export function getComponentConfig(type) {
  return COMPONENT_TYPES[type] || null
}

/**
 * Get all component types as array
 * @returns {Array} Array of component configs
 */
export function getComponentList() {
  return Object.values(COMPONENT_TYPES)
}

/**
 * Get components filtered by category
 * @param {string} category - Category key
 * @returns {Array} Filtered components
 */
export function getComponentsByCategory(category) {
  if (!category || category === 'all') {
    return getComponentList()
  }
  return getComponentList().filter(c => c.category === category)
}

/**
 * Get sorted category list
 * @returns {Array} Sorted categories
 */
export function getCategoryList() {
  return Object.values(COMPONENT_CATEGORIES)
    .sort((a, b) => a.order - b.order)
}

/**
 * Create a new component instance with default props
 * @param {string} type - Component type
 * @param {number} counter - Counter for unique ID
 * @returns {Object} New component instance
 */
export function createComponentInstance(type, counter) {
  const config = getComponentConfig(type)
  if (!config) return null

  return {
    type,
    id: `${type}_${counter}`,
    label: `${type.charAt(0).toUpperCase() + type.slice(1)} ${counter}`,
    ...JSON.parse(JSON.stringify(config.defaultProps))
  }
}

export default {
  COMPONENT_TYPES,
  COMPONENT_CATEGORIES,
  getComponentConfig,
  getComponentList,
  getComponentsByCategory,
  getCategoryList,
  createComponentInstance
}
