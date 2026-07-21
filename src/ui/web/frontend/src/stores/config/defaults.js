/**
 * Config Store Defaults
 *
 * S-Grade: Default configuration values.
 * Single responsibility: Fallback values when backend unavailable.
 *
 * NOTE: These are FALLBACKS only. Backend is the source of truth.
 */

export const DEFAULTS = {
  // =============================================================================
  // Timing Configuration
  // =============================================================================
  timing: {
    polling: {
      executionStatus: 1000,
      debugStatus: 1000,
      replay: 1000,
      recording: 3000,
      default: 2000,
    },
    notifications: {
      successDuration: 3000,
      warningDuration: 4000,
      errorDuration: 5000,
      infoDuration: 3000,
    },
    debounce: {
      search: 300,
      input: 200,
      resize: 100,
    },
    animation: {
      transition: 200,
      fade: 150,
    },
  },

  // =============================================================================
  // Layout Configuration
  // =============================================================================
  layout: {
    workflow: {
      horizontalSpacing: 320,
      verticalSpacing: 150,
      initialX: 200,
      initialY: 100,
      nodeWidth: 280,
      nodeHeight: 120,
    },
    canvas: {
      minZoom: 0.1,
      maxZoom: 2.0,
      defaultZoom: 1.0,
      fitPadding: 50,
    },
  },

  // =============================================================================
  // Theme Configuration
  // =============================================================================
  theme: {
    colors: {
      primary: '#3b82f6',
      secondary: '#8b5cf6',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#3b82f6',
    },
    particles: {
      colors: ['#3b82f6', '#8b5cf6', '#06b6d4'],
      count: 50,
      speed: 1.0,
    },
    charts: {
      palette: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
    },
    status: {
      running: '#3b82f6',
      success: '#10b981',
      failed: '#ef4444',
      pending: '#6b7280',
      cancelled: '#9ca3af',
    },
  },

  // =============================================================================
  // Limits Configuration
  // =============================================================================
  limits: {
    logs: {
      maxEntries: 1000,
      maxLineLength: 10000,
    },
    files: {
      maxSizeBytes: 10485760,
      allowedTypes: ['image/*', 'application/pdf', '.json', '.yaml', '.yml'],
    },
    strings: {
      maxNameLength: 255,
      maxDescriptionLength: 2000,
    },
    pagination: {
      defaultPageSize: 20,
      availableSizes: [10, 20, 50, 100],
    },
    workflow: {
      maxSteps: 100,
      maxParallelExecutions: 10,
    },
  },

  // =============================================================================
  // Shortcuts Configuration
  // =============================================================================
  shortcuts: {
    workflow: {
      save: 'Ctrl+S',
      undo: 'Ctrl+Z',
      redo: 'Ctrl+Shift+Z',
      delete: 'Delete',
      copy: 'Ctrl+C',
      paste: 'Ctrl+V',
      selectAll: 'Ctrl+A',
      deselect: 'Escape',
      fitView: 'Ctrl+0',
      zoomIn: 'Ctrl+=',
      zoomOut: 'Ctrl+-',
    },
    global: {
      search: 'Ctrl+K',
      help: 'F1',
      settings: 'Ctrl+,',
    },
  },

  // =============================================================================
  // LLM Configuration
  // =============================================================================
  llm: {
    providers: [],
    defaults: {
      provider: 'openai',
      model: 'gpt-4o',
      temperature: 0.7,
      maxTokens: 1000,
    },
  },

  // =============================================================================
  // Triggers Configuration
  // =============================================================================
  triggers: {
    types: [],
    defaults: {
      triggerType: 'manual',
    },
  },

  // =============================================================================
  // HTTP Configuration
  // =============================================================================
  http: {
    methods: [],
    authTypes: [],
    bodyTypes: [],
    defaults: {
      method: 'GET',
      authType: 'none',
      bodyType: 'none',
      timeout: 30000,
    },
  },

  // =============================================================================
  // Parameter Type Mappings
  // =============================================================================
  paramTypes: {},
  outputTypes: {},

  // =============================================================================
  // Marketplace Configuration
  // =============================================================================
  marketplace: {
    categories: [],
    templateStatus: {},
    visibilityOptions: [],
    mutabilityOptions: [],
    currencies: [],
    priceSuggestions: [],
    inviteKeyUsageOptions: [],
  },

  // =============================================================================
  // Subscription Configuration
  // =============================================================================
  subscription: {
    plans: [],
    statuses: [],
  },

  // =============================================================================
  // Workflow Types Configuration
  // =============================================================================
  workflowTypes: {
    nodeTypes: [],
    edgeTypes: [],
    portTypes: [],
  },

  // =============================================================================
  // Form Types Configuration
  // =============================================================================
  formTypes: {
    formTypes: [],
    inputTypes: [],
    outputTypes: [],
    bindingSources: [],
  },

  // =============================================================================
  // Countries Configuration
  // =============================================================================
  countries: [],

  // =============================================================================
  // Quick Start Configuration
  // =============================================================================
  quickStart: {
    modules: [],
    onboardingSteps: [],
  },

  // =============================================================================
  // Messaging Providers Configuration
  // =============================================================================
  messaging: {
    providers: [],
  },

  // =============================================================================
  // Breakpoints Configuration
  // =============================================================================
  breakpoints: {
    types: [],
    actions: [],
  },

  // =============================================================================
  // Node Design Configuration (dimensions SSOT from backend)
  // =============================================================================
  nodeDesign: {
    standard:  { dimensions: { shape: 'rectangle',  width: 240, height: 76 } },
    trigger:   { dimensions: { shape: 'semicircle', width: 120, height: 76 } },
    start:     { dimensions: { shape: 'rectangle',  width: 240, height: 76 } },
    end:       { dimensions: { shape: 'rectangle',  width: 240, height: 76 } },
    branch:    { dimensions: { shape: 'diamond',    width: 76,  height: 76 } },
    switch:    { dimensions: { shape: 'diamond',    width: 76,  height: 76 } },
    loop:      { dimensions: { shape: 'hexagon',    width: 76,  height: 76 } },
    container: { dimensions: { shape: 'container',  width: 90,  height: 90 } },
    ai_agent:  { dimensions: { shape: 'rectangle',  width: 240, height: 76 } },
    ai_sub:    { dimensions: { shape: 'pill',       width: 72,  height: 56 } },
  },
}
