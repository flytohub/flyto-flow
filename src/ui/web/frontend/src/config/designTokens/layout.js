/**
 * Design Tokens - Layout Constants
 * Panel dimensions, component sizes, border radius, z-index
 */

export const LAYOUT = Object.freeze({
  // Panel dimensions
  PANEL: {
    TOOLBOX_WIDTH: 280,
    TOOLBOX_MIN_WIDTH: 240,
    TOOLBOX_MAX_WIDTH: 360,
    PROPERTIES_WIDTH: 400,
    PROPERTIES_MIN_WIDTH: 320,
    PROPERTIES_MAX_WIDTH: 520,
    CANVAS_MIN_WIDTH: 600,
    HEADER_HEIGHT: 56,
    TAB_HEIGHT: 44,
  },

  // Component constraints
  COMPONENT: {
    MAX_LINES: 500,
    ICON_SIZE_XS: 12,
    ICON_SIZE_SM: 14,
    ICON_SIZE_MD: 16,
    ICON_SIZE_LG: 18,
    ICON_SIZE_XL: 20,
    ICON_SIZE_2XL: 24,
  },

  // Grid system
  GRID: {
    COLUMNS: 12,
    GAP: 16,
    CONTAINER_PADDING: 24,
  },

  // Border radius
  RADIUS: {
    XS: 2,
    SM: 4,
    MD: 6,
    LG: 8,
    XL: 12,
    FULL: 9999,
  },

  // Z-index layers
  Z_INDEX: {
    BASE: 0,
    DROPDOWN: 100,
    STICKY: 150,
    MODAL_BACKDROP: 200,
    MODAL: 250,
    DIALOG: 300,
    POPOVER: 350,
    TOOLTIP: 400,
    TOAST: 500,
  },

  // Aspect ratios (width:height)
  ASPECT_RATIO: {
    SQUARE: 1,
    VIDEO: 16 / 9,
    PHOTO: 4 / 3,
    PORTRAIT: 3 / 4,
  },
})
