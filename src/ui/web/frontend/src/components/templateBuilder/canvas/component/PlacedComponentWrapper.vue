<template>
  <div
    :class="[
      'placed-component-wrapper',
      { selected: isSelected, dragging: isDragging }
    ]"
    :style="wrapperStyle"
    @click.stop="handleWrapperClick"
  >
    <!-- Header with type icon, label, and actions -->
    <div v-if="showHeader" class="component-header">
      <div class="header-left">
        <span class="component-icon" :style="{ color: componentColor }" aria-hidden="true">
          <component :is="iconComponent" :size="14" />
        </span>
        <span class="component-type">{{ componentLabel }}</span>
      </div>
      <div class="header-actions">
        <button
          type="button"
          class="action-btn settings-btn"
          :title="$t('templateBuilder.settings')"
          :aria-label="$t('templateBuilder.settings')"
          @click.stop="handleSettingsClick"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </button>
        <button
          v-if="showDuplicateAction"
          type="button"
          class="action-btn duplicate-btn"
          :title="$t('templateBuilder.duplicate')"
          :aria-label="$t('templateBuilder.duplicate')"
          @click.stop="handleDuplicateClick"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
        </button>
        <button
          v-if="showDeleteAction"
          type="button"
          class="action-btn delete-btn"
          :title="$t('templateBuilder.delete')"
          :aria-label="$t('templateBuilder.delete')"
          @click.stop="handleDeleteClick"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Preview Content - Direct editable -->
    <div class="component-content">
      <PreviewRenderer
        :component="component"
        :editable="editable && !isDragging"
        @update="handlePreviewUpdate"
        @focus="handlePreviewFocus"
        @blur="handlePreviewBlur"
        @click="handlePreviewClick"
      />
    </div>

    <!-- Drag handle (visible on hover/selected) -->
    <div
      v-if="showDragHandle"
      class="drag-handle"
      @mousedown="handleDragStart"
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
        <circle cx="8" cy="6" r="2" />
        <circle cx="16" cy="6" r="2" />
        <circle cx="8" cy="12" r="2" />
        <circle cx="16" cy="12" r="2" />
        <circle cx="8" cy="18" r="2" />
        <circle cx="16" cy="18" r="2" />
      </svg>
    </div>

    <!-- Selection indicator -->
    <div v-if="isSelected" class="selection-indicator" :style="{ borderColor: componentColor }" />
  </div>
</template>

<script setup>
import { computed, ref, shallowRef, defineAsyncComponent } from 'vue'
import { getComponentConfig } from '../../_config/componentRegistry'
import { getComponentColor } from '../../_config/colorPalette'
import PreviewRenderer from './previews/PreviewRenderer.vue'

const props = defineProps({
  component: {
    type: Object,
    required: true
  },
  isSelected: {
    type: Boolean,
    default: false
  },
  editable: {
    type: Boolean,
    default: true
  },
  isDragging: {
    type: Boolean,
    default: false
  },
  showHeader: {
    type: Boolean,
    default: true
  },
  showDragHandle: {
    type: Boolean,
    default: true
  },
  showDuplicateAction: {
    type: Boolean,
    default: true
  },
  showDeleteAction: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits([
  'select',
  'open-settings',
  'update',
  'duplicate',
  'delete',
  'drag-start',
  'focus',
  'blur'
])

// Get component configuration
const componentConfig = computed(() => {
  return getComponentConfig(props.component.type)
})

// Get component color
const componentColor = computed(() => {
  return getComponentColor(props.component.type)
})

// Get component label from config or component
const componentLabel = computed(() => {
  if (componentConfig.value?.labelKey) {
    return componentConfig.value.labelKey.split('.').pop()
  }
  return props.component.type
})

// Dynamic icon component (lazy loaded)
const iconMap = {
  TextCursorInput: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.TextCursorInput)),
  Hash: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Hash)),
  Mail: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Mail)),
  Lock: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Lock)),
  Link: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Link)),
  Phone: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Phone)),
  AlignLeft: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.AlignLeft)),
  ChevronDown: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.ChevronDown)),
  CheckSquare: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.CheckSquare)),
  Circle: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Circle)),
  ToggleLeft: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.ToggleLeft)),
  Calendar: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Calendar)),
  Clock: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Clock)),
  Sliders: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Sliders)),
  Star: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Star)),
  Upload: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Upload)),
  Heading: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Heading)),
  Type: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Type)),
  Minus: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Minus)),
  Image: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.Image)),
  MousePointer: defineAsyncComponent(() => import('lucide-vue-next').then(m => m.MousePointer))
}

const iconComponent = computed(() => {
  const iconName = componentConfig.value?.icon || 'Type'
  return iconMap[iconName] || iconMap.Type
})

// Wrapper style
const wrapperStyle = computed(() => {
  return {
    '--component-color': componentColor.value
  }
})

// Event handlers
function handleWrapperClick(e) {
  emit('select', props.component.id)
}

function handleSettingsClick() {
  emit('open-settings', props.component.id)
}

function handleDuplicateClick() {
  emit('duplicate', props.component.id)
}

function handleDeleteClick() {
  emit('delete', props.component.id)
}

function handleDragStart(e) {
  emit('drag-start', e, props.component.id)
}

function handlePreviewUpdate(payload) {
  emit('update', {
    componentId: props.component.id,
    ...payload
  })
}

function handlePreviewFocus() {
  emit('focus', props.component.id)
}

function handlePreviewBlur() {
  emit('blur', props.component.id)
}

function handlePreviewClick() {
  // Preview click is handled by direct editing
}
</script>

<style scoped>
.placed-component-wrapper {
  position: relative;
  padding: 12px;
  border-radius: 8px;
  background: rgba(30, 41, 59, 0.3);
  border: 1px solid transparent;
  transition: all 0.2s;
  cursor: default;
}

.placed-component-wrapper:hover {
  background: rgba(30, 41, 59, 0.5);
  border-color: rgba(71, 85, 105, 0.5);
}

.placed-component-wrapper.selected {
  background: rgba(30, 41, 59, 0.6);
  border-color: var(--component-color, #8B5CF6);
}

.placed-component-wrapper.dragging {
  opacity: 0.5;
  cursor: grabbing;
}

/* Header */
.component-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.component-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.component-type {
  font-size: 11px;
  font-weight: 500;
  color: #94a3b8;
  text-transform: capitalize;
}

/* Header Actions */
.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.placed-component-wrapper:hover .header-actions,
.placed-component-wrapper.selected .header-actions {
  opacity: 1;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  min-height: 32px;
  padding: 4px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}

.action-btn:focus-visible {
  outline: 2px solid #8B5CF6;
  outline-offset: 2px;
}

.action-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
}

.settings-btn:hover {
  color: #8B5CF6;
}

.duplicate-btn:hover {
  color: #3B82F6;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* Content */
.component-content {
  position: relative;
}

/* Drag Handle */
.drag-handle {
  position: absolute;
  left: -8px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 32px;
  background: rgba(30, 41, 59, 0.9);
  border: 1px solid #475569;
  border-radius: 4px;
  color: #64748b;
  cursor: grab;
  opacity: 0;
  transition: opacity 0.2s;
}

.placed-component-wrapper:hover .drag-handle,
.placed-component-wrapper.selected .drag-handle {
  opacity: 1;
}

.drag-handle:hover {
  color: #94a3b8;
  border-color: #64748b;
}

.drag-handle:active {
  cursor: grabbing;
}

/* Selection Indicator */
.selection-indicator {
  position: absolute;
  inset: -2px;
  border: 2px solid var(--component-color, #8B5CF6);
  border-radius: 10px;
  pointer-events: none;
}
</style>
