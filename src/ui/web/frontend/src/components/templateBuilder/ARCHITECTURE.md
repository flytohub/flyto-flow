# TemplateBuilder Architecture Analysis & Refactoring Plan

## Current Structure Analysis

### Main Components (36 files)

```
TemplateBuilder.vue (1150 lines) - Main page orchestrator
├── BuilderHeader.vue          - Header with actions
├── BuilderTabBar.vue          - Tab navigation (UI/Workflow)
├── SaveConfirmDialog.vue      - Save confirmation modal
├── AIChatWindow.vue           - AI assistant chat
├── TerminalLogDialog.vue      - Terminal output viewer
│
├── UIDesignTab.vue (963 lines) - UI Design canvas [NEEDS REFACTOR]
│   ├── Toolbox panel (inline)
│   ├── Canvas area (inline)
│   ├── Layout picker (inline)
│   └── ComponentPropertiesPanel.vue - Properties editor
│
├── WorkflowTab.vue            - Workflow editor
│   ├── WorkflowCanvas.vue
│   ├── CollapseHandle.vue
│   ├── PanelHeader.vue
│   ├── NodeBasicInfo.vue
│   ├── NodeDescription.vue
│   ├── NodeExecutionSettings.vue
│   ├── FormInputParams.vue
│   ├── GenericParams.vue
│   ├── DeleteNodeButton.vue
│   └── EmptyPropertiesPanel.vue
│
├── GridEditDialog.vue         - Grid ratio editor
├── TestModal.vue              - Test results
├── ConfirmDialog.vue          - Generic confirmation
├── ToastNotification.vue      - Toast notifications
└── ModuleSelector.vue         - Module selection modal
```

### Identified Issues

#### 1. UIDesignTab.vue is Monolithic (963 lines)
- Contains toolbox, canvas, sections, columns, components all inline
- Hardcoded component list (lines 348-369)
- Hardcoded colors (lines 422-429)
- Mixed concerns: layout + data + presentation

#### 2. Click Behavior Issue
**Current:** Click on placed component -> Opens properties panel
**Desired:**
- Click on component -> Direct edit (input value, select option, etc.)
- Click on settings icon -> Opens properties panel

#### 3. No Live Preview
- PlacedComponent.vue only shows: icon + label + ID
- No actual rendered preview of input/select/checkbox etc.

#### 4. Missing Features
- No image preview for image-related components
- No column visibility toggle
- No drag-to-reorder components within column

#### 5. Hardcoded Values
- Component types hardcoded in UIDesignTab
- Colors hardcoded
- No registry/config pattern

---

## Proposed Atomic Architecture

### Design Principles
1. **Single Responsibility** - Each component does ONE thing
2. **Zero Coupling** - Components communicate via props/events only
3. **Registry Pattern** - Component types defined in config, not inline
4. **Composable State** - Shared state via composables

### New Directory Structure

```
src/components/templateBuilder/
├── _config/                          # Configuration (no UI)
│   ├── componentRegistry.js          # Component type definitions
│   ├── colorPalette.js               # Color constants
│   └── iconMap.js                    # Icon mappings
│
├── _composables/                     # Shared state/logic
│   ├── useTemplateState.js           # Template data state
│   ├── useSelectionState.js          # Selection management
│   ├── useComponentActions.js        # CRUD operations
│   └── useDragDrop.js                # Drag/drop logic
│
├── primitives/                       # Atomic UI building blocks
│   ├── BaseInput.vue                 # Basic input wrapper
│   ├── BaseButton.vue                # Basic button
│   ├── BaseSelect.vue                # Basic select
│   ├── IconButton.vue                # Icon-only button
│   ├── Badge.vue                     # Status badge
│   ├── CollapsibleSection.vue        # Collapsible wrapper
│   └── SlidePanel.vue                # Slide-out panel base
│
├── toolbox/                          # Component toolbox area
│   ├── ToolboxContainer.vue          # Main container
│   ├── ToolboxHeader.vue             # Header with icon
│   ├── ToolboxSearch.vue             # Search input
│   ├── CategoryFilter.vue            # Category pills
│   ├── ComponentGrid.vue             # Grid layout
│   ├── ComponentCard.vue             # Single draggable card
│   └── EmptyToolbox.vue              # Empty state
│
├── canvas/                           # Canvas editing area
│   ├── CanvasContainer.vue           # Main wrapper
│   ├── CanvasHeader.vue              # Header with actions
│   ├── CanvasContent.vue             # Scrollable content
│   ├── EmptyCanvas.vue               # Empty state
│   │
│   ├── layout/                       # Layout selection
│   │   ├── LayoutPickerButton.vue    # Trigger button
│   │   ├── LayoutPickerDropdown.vue  # Dropdown menu
│   │   └── LayoutOption.vue          # Single option
│   │
│   ├── section/                      # Section components
│   │   ├── SectionBlock.vue          # Section wrapper
│   │   ├── SectionToolbar.vue        # Toolbar with actions
│   │   ├── SectionInfo.vue           # Info display (columns, grid)
│   │   ├── SectionActions.vue        # Action buttons
│   │   └── SectionColumns.vue        # Column grid container
│   │
│   ├── column/                       # Column components
│   │   ├── ColumnDropZone.vue        # Droppable area
│   │   ├── ColumnEmpty.vue           # Empty placeholder
│   │   └── ColumnVisibilityToggle.vue # Show/hide toggle
│   │
│   └── component/                    # Placed components
│       ├── PlacedComponentWrapper.vue    # Wrapper with selection
│       ├── PlacedComponentHeader.vue     # Icon + label + settings
│       ├── PlacedComponentActions.vue    # Delete, reorder buttons
│       │
│       └── previews/                     # Live preview renderers
│           ├── PreviewRenderer.vue       # Dynamic renderer
│           ├── InputPreview.vue          # Text input (editable)
│           ├── NumberPreview.vue         # Number input
│           ├── EmailPreview.vue          # Email input
│           ├── PasswordPreview.vue       # Password input
│           ├── UrlPreview.vue            # URL input
│           ├── TextareaPreview.vue       # Textarea
│           ├── SelectPreview.vue         # Dropdown select
│           ├── CheckboxPreview.vue       # Checkbox
│           ├── RadioPreview.vue          # Radio group
│           ├── SwitchPreview.vue         # Toggle switch
│           ├── DatePreview.vue           # Date picker
│           ├── TimePreview.vue           # Time picker
│           ├── RangePreview.vue          # Slider
│           ├── RatingPreview.vue         # Star rating
│           ├── FilePreview.vue           # File upload
│           ├── ImagePreview.vue          # Image display [NEW]
│           ├── HeadingPreview.vue        # Heading text
│           ├── TextPreview.vue           # Static text
│           ├── DividerPreview.vue        # Horizontal line
│           └── ButtonPreview.vue         # Button
│
├── properties/                       # Properties panel
│   ├── PropertiesPanelContainer.vue  # Main slide-out panel
│   ├── PropertiesPanelHeader.vue     # Header with close
│   ├── PropertiesPanelBody.vue       # Scrollable content
│   │
│   ├── groups/                       # Property groups
│   │   ├── PropertyGroup.vue         # Group wrapper
│   │   ├── IdPropertyGroup.vue       # Component ID
│   │   ├── LabelPropertyGroup.vue    # Label + placeholder
│   │   ├── DefaultValueGroup.vue     # Default value
│   │   ├── InputTypeGroup.vue        # Input type selector
│   │   ├── OptionsGroup.vue          # Select/radio options
│   │   ├── ButtonPropertiesGroup.vue # Button specific
│   │   ├── ValidationGroup.vue       # Validation rules
│   │   └── ConditionalGroup.vue      # Conditional display
│   │
│   └── fields/                       # Property field types
│       ├── PropertyRow.vue           # Row layout
│       ├── PropertyLabel.vue         # Field label
│       ├── PropertyInput.vue         # Text input
│       ├── PropertySelect.vue        # Select dropdown
│       ├── PropertyCheckbox.vue      # Checkbox
│       ├── PropertyTextarea.vue      # Textarea
│       ├── SettingsToggleButton.vue  # Settings expand button
│       └── ExpandableOptions.vue     # Expandable section
│
├── workflow/                         # Workflow tab (existing)
│   └── ... (keep existing structure)
│
├── dialogs/                          # Modal dialogs
│   ├── BaseDialog.vue                # Base dialog wrapper
│   ├── SaveConfirmDialog.vue
│   ├── GridEditDialog.vue
│   ├── TestModal.vue
│   ├── ConfirmDialog.vue
│   └── TerminalLogDialog.vue
│
├── header/                           # Header components
│   ├── BuilderHeader.vue
│   ├── BuilderTabBar.vue
│   └── HeaderActionButton.vue
│
└── common/                           # Shared components
    ├── ToastNotification.vue
    └── AIChatWindow.vue
```

---

## Key Refactoring Tasks

### Phase 1: Configuration & State

#### Task 1.1: Create Component Registry
```javascript
// _config/componentRegistry.js
export const COMPONENT_TYPES = {
  input: {
    type: 'input',
    label: 'Text Input',
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
  // ... more types
}

export const COMPONENT_CATEGORIES = {
  'basic-input': { label: 'Basic Input', order: 1 },
  'selectors': { label: 'Selectors', order: 2 },
  // ...
}
```

#### Task 1.2: Create Color Palette
```javascript
// _config/colorPalette.js
export const COLORS = {
  input: '#3B82F6',
  textarea: '#06B6D4',
  select: '#8B5CF6',
  checkbox: '#10B981',
  radio: '#F59E0B',
  button: '#EC4899',
  // ...
}
```

#### Task 1.3: Create Selection State Composable
```javascript
// _composables/useSelectionState.js
export function useSelectionState() {
  const selectedSection = ref(null)
  const selectedColumn = ref(null)
  const selectedComponentLocation = ref(null)

  // ... methods

  return {
    selectedSection,
    selectedColumn,
    selectedComponentLocation,
    selectSection,
    selectColumn,
    selectComponent,
    clearSelection
  }
}
```

### Phase 2: Primitives

#### Task 2.1: Create BaseInput
```vue
<!-- primitives/BaseInput.vue -->
<template>
  <input
    :type="type"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :readonly="readonly"
    class="base-input"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>
```

### Phase 3: Toolbox Refactor

#### Task 3.1: ToolboxContainer
- Compose: ToolboxHeader + ToolboxSearch + CategoryFilter + ComponentGrid
- No inline logic, just composition

#### Task 3.2: ComponentCard
- Draggable card
- Uses registry for icon/color/label

### Phase 4: Canvas Refactor

#### Task 4.1: PlacedComponentWrapper (CRITICAL)
```vue
<template>
  <div class="placed-component" :class="{ selected }">
    <PlacedComponentHeader
      :icon="componentConfig.icon"
      :label="component.label"
      @settings-click="$emit('open-properties')"
    />

    <!-- Live Preview - Supports Direct Editing -->
    <PreviewRenderer
      :type="component.type"
      :component="component"
      :editable="true"
      @update="$emit('update-component', $event)"
    />

    <PlacedComponentActions
      @delete="$emit('delete')"
      @move-up="$emit('move-up')"
      @move-down="$emit('move-down')"
    />
  </div>
</template>
```

#### Task 4.2: PreviewRenderer (Dynamic)
```vue
<template>
  <component
    :is="previewComponent"
    :component="component"
    :editable="editable"
    @update="$emit('update', $event)"
  />
</template>

<script setup>
import { computed } from 'vue'
import { COMPONENT_TYPES } from '../_config/componentRegistry'

// Dynamic import based on type
const previewComponent = computed(() => {
  const config = COMPONENT_TYPES[props.component.type]
  return config?.previewComponent || 'div'
})
</script>
```

#### Task 4.3: InputPreview (Direct Editable)
```vue
<template>
  <div class="input-preview">
    <label v-if="component.label" class="preview-label">
      {{ component.label }}
    </label>
    <input
      :type="component.inputType || 'text'"
      :value="component.default"
      :placeholder="component.placeholder"
      class="preview-input"
      @input="handleInput"
    />
  </div>
</template>

<script setup>
const emit = defineEmits(['update'])

function handleInput(e) {
  emit('update', { ...props.component, default: e.target.value })
}
</script>
```

### Phase 5: Properties Panel Refactor

#### Task 5.1: Split into Property Groups
- Each property group is a separate component
- Uses SettingsToggleButton for expand/collapse

### Phase 6: Integration

#### Task 6.1: Compose UIDesignTab
```vue
<template>
  <div class="ui-design-container">
    <ToolboxContainer
      :selected-section="selectedSection"
      :selected-column="selectedColumn"
      @add-component="handleAddComponent"
    />

    <CanvasContainer
      :sections="sections"
      :selected-section="selectedSection"
      :selected-column="selectedColumn"
      :selected-component="selectedComponentLocation"
      @select-section="selectSection"
      @select-column="selectColumn"
      @select-component="selectComponent"
      @open-properties="openPropertiesForComponent"
      @update-component="updateComponent"
    />

    <PropertiesPanelContainer
      v-if="showPropertiesPanel"
      :component="selectedComponentObj"
      @close="closeProperties"
      @update="updateComponent"
    />
  </div>
</template>
```

---

## Behavior Changes

### Click on Placed Component
**Before:** Opens properties panel
**After:**
1. Click on preview area -> Direct edit (if supported)
2. Click on settings icon -> Opens properties panel
3. Click elsewhere on component -> Select component

### Component Rendering
**Before:** Icon + Label + ID only
**After:** Full live preview with actual form controls

### Column Layout
**Before:** Always visible
**After:** Toggle visibility per section (for collapsed view)

---

## Migration Strategy

1. Create new components alongside existing
2. Test each atomic component in isolation
3. Replace UIDesignTab piece by piece
4. Remove old inline code after verification
5. Update imports in TemplateBuilder.vue

---

## Files to Create (Priority Order)

### Phase 1 (Config)
1. `_config/componentRegistry.js`
2. `_config/colorPalette.js`
3. `_config/iconMap.js`

### Phase 2 (Composables)
4. `_composables/useSelectionState.js`
5. `_composables/useComponentActions.js`

### Phase 3 (Previews)
6. `canvas/component/previews/PreviewRenderer.vue`
7. `canvas/component/previews/InputPreview.vue`
8. `canvas/component/previews/SelectPreview.vue`
9. `canvas/component/previews/CheckboxPreview.vue`
10. ... other previews

### Phase 4 (Wrappers)
11. `canvas/component/PlacedComponentWrapper.vue`
12. `canvas/component/PlacedComponentHeader.vue`
13. `canvas/component/PlacedComponentActions.vue`

### Phase 5 (Integration)
14. Update `UIDesignTab.vue` to use new components

---

## Questions for Discussion

1. **Image Preview**: What image sources should be supported?
   - URL input
   - Base64
   - File upload preview

2. **Column Visibility**: Should collapsed columns show:
   - Nothing
   - Indicator badge with count
   - Mini preview

3. **Drag Reorder**: Within column, should components be:
   - Draggable
   - Use up/down arrows only
   - Both

4. **Validation Preview**: Show validation errors inline in preview?

5. **Component Groups**: Should components support grouping within a column?
