<template>
  <div
    :class="['var-item', { selected, dragging }]"
    @click="$emit('select', variable)"
    draggable="true"
    @dragstart="handleDragStart"
    @dragend="handleDragEnd"
  >
    <div class="var-icon">
      <component :is="icon" :size="14" />
    </div>
    <div class="var-info">
      <span class="var-label">{{ variable.label }}</span>
      <span class="var-path">{{ variable.expression }}</span>
    </div>
    <span :class="['var-type', `type-${variable.dataType}`]">
      {{ variable.dataType }}
    </span>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Type, Hash, ToggleLeft, Image, FileText, Layers, Package } from 'lucide-vue-next'
import { DATA_TYPES } from '@/constants/templateBuilder/bindingTypes'

const TYPE_ICONS = {
  [DATA_TYPES.STRING]: Type,
  [DATA_TYPES.NUMBER]: Hash,
  [DATA_TYPES.BOOLEAN]: ToggleLeft,
  [DATA_TYPES.IMAGE]: Image,
  [DATA_TYPES.FILE]: FileText,
  [DATA_TYPES.ARRAY]: Layers,
  [DATA_TYPES.OBJECT]: Package
}

const props = defineProps({
  variable: { type: Object, required: true },
  selected: { type: Boolean, default: false }
})

defineEmits(['select'])

const icon = computed(() => TYPE_ICONS[props.variable.dataType] || Type)

// Drag state
const dragging = ref(false)

// Drag handlers
function handleDragStart(event) {
  dragging.value = true
  // Set drag data as the variable expression
  event.dataTransfer.setData('text/plain', props.variable.expression)
  event.dataTransfer.setData('application/x-flyto-variable', JSON.stringify({
    expression: props.variable.expression,
    label: props.variable.label,
    dataType: props.variable.dataType
  }))
  event.dataTransfer.effectAllowed = 'copy'
}

function handleDragEnd() {
  dragging.value = false
}
</script>

<style scoped>
.var-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(30, 41, 59, 0.4);
  border: 1px solid rgba(71, 85, 105, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 6px;
}

.var-item:last-child { margin-bottom: 0; }

.var-item:hover {
  background: rgba(71, 85, 105, 0.3);
  border-color: rgba(139, 92, 246, 0.3);
}

.var-item.selected {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.5);
}

.var-item.dragging {
  opacity: 0.6;
  cursor: grabbing;
}

.var-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: rgba(71, 85, 105, 0.4);
  border-radius: 6px;
  color: #94a3b8;
  flex-shrink: 0;
}

.var-item.selected .var-icon {
  background: rgba(139, 92, 246, 0.3);
  color: #a78bfa;
}

.var-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.var-label {
  font-size: 13px;
  font-weight: 500;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.var-path {
  font-size: 10px;
  font-family: 'SF Mono', Monaco, monospace;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.var-type {
  padding: 3px 8px;
  background: rgba(71, 85, 105, 0.4);
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  flex-shrink: 0;
}

.var-type.type-string { background: rgba(6, 182, 212, 0.2); color: #22d3ee; }
.var-type.type-number { background: rgba(251, 146, 60, 0.2); color: #fb923c; }
.var-type.type-boolean { background: rgba(168, 85, 247, 0.2); color: #c084fc; }
.var-type.type-image { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.var-type.type-file { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
</style>
