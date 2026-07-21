<template>
  <div class="preview-renderer" @click.stop="handlePreviewClick">
    <component
      v-if="previewComponent"
      :is="previewComponent"
      :component="component"
      :editable="editable && supportsDirectEdit"
      @update="handleUpdate"
      @focus="handleFocus"
      @blur="handleBlur"
      @click="handleClick"
    />
    <div v-else class="fallback-preview">
      <span class="fallback-type">{{ component.type }}</span>
      <span class="fallback-label">{{ component.label }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent, shallowRef } from 'vue'
import { getComponentConfig } from '../../../_config/componentRegistry'

const props = defineProps({
  component: {
    type: Object,
    required: true
  },
  editable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update', 'focus', 'blur', 'click', 'preview-click'])

// Get component config
const componentConfig = computed(() => {
  return getComponentConfig(props.component.type)
})

// Check if component supports direct editing
const supportsDirectEdit = computed(() => {
  return componentConfig.value?.supportsDirectEdit || false
})

// Preview component map - lazy loaded
const previewComponents = {
  InputPreview: defineAsyncComponent(() => import('./InputPreview.vue')),
  NumberPreview: defineAsyncComponent(() => import('./InputPreview.vue')), // Reuse InputPreview
  EmailPreview: defineAsyncComponent(() => import('./InputPreview.vue')),
  PasswordPreview: defineAsyncComponent(() => import('./InputPreview.vue')),
  UrlPreview: defineAsyncComponent(() => import('./InputPreview.vue')),
  TelPreview: defineAsyncComponent(() => import('./InputPreview.vue')),
  TextareaPreview: defineAsyncComponent(() => import('./TextareaPreview.vue')),
  SelectPreview: defineAsyncComponent(() => import('./SelectPreview.vue')),
  CheckboxPreview: defineAsyncComponent(() => import('./CheckboxPreview.vue')),
  RadioPreview: defineAsyncComponent(() => import('./RadioPreview.vue')),
  SwitchPreview: defineAsyncComponent(() => import('./SwitchPreview.vue')),
  DatePreview: defineAsyncComponent(() => import('./DatePreview.vue')),
  TimePreview: defineAsyncComponent(() => import('./TimePreview.vue')),
  RangePreview: defineAsyncComponent(() => import('./RangePreview.vue')),
  RatingPreview: defineAsyncComponent(() => import('./RatingPreview.vue')),
  FilePreview: defineAsyncComponent(() => import('./FilePreview.vue')),
  ColorPreview: defineAsyncComponent(() => import('./ColorPreview.vue')),
  DatetimePreview: defineAsyncComponent(() => import('./DatetimePreview.vue')),
  PathPreview: defineAsyncComponent(() => import('./PathPreview.vue')),
  ArrayPreview: defineAsyncComponent(() => import('./ArrayPreview.vue')),
  KeyValuePreview: defineAsyncComponent(() => import('./KeyValuePreview.vue')),
  JsonPreview: defineAsyncComponent(() => import('./JsonPreview.vue')),
  HeadingPreview: defineAsyncComponent(() => import('./HeadingPreview.vue')),
  TextPreview: defineAsyncComponent(() => import('./TextPreview.vue')),
  DividerPreview: defineAsyncComponent(() => import('./DividerPreview.vue')),
  ImagePreview: defineAsyncComponent(() => import('./ImagePreview.vue')),
  ButtonPreview: defineAsyncComponent(() => import('./ButtonPreview.vue'))
}

// Get the preview component for current type
const previewComponent = computed(() => {
  const config = componentConfig.value
  if (!config) return null

  const componentName = config.previewComponent
  return previewComponents[componentName] || null
})

function handleUpdate(payload) {
  emit('update', payload)
}

function handleFocus() {
  emit('focus')
}

function handleBlur() {
  emit('blur')
}

function handleClick() {
  emit('click')
}

function handlePreviewClick(e) {
  emit('preview-click', e)
}
</script>

<style scoped>
.preview-renderer {
  width: 100%;
  min-height: 32px;
}

.fallback-preview {
  padding: 8px 12px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px dashed #475569;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.fallback-type {
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  background: rgba(71, 85, 105, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
}

.fallback-label {
  font-size: 12px;
  color: #94a3b8;
}
</style>
