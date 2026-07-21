<template>
  <div class="canvas-controls">
    <button @click="$emit('zoom-in')" class="control-btn" :title="$t('workflowCanvas.controls.zoomIn')">
      <ZoomIn :size="16" />
    </button>
    <button @click="$emit('zoom-out')" class="control-btn" :title="$t('workflowCanvas.controls.zoomOut')">
      <ZoomOut :size="16" />
    </button>
    <button @click="$emit('fit-view')" class="control-btn" :title="$t('workflowCanvas.controls.fitView')">
      <Maximize2 :size="16" />
    </button>
    <button @click="$emit('auto-layout')" class="control-btn" :title="$t('workflowCanvas.controls.autoLayout')">
      <LayoutGrid :size="16" />
    </button>

    <!-- Alignment Tools (visible when 2+ nodes selected) -->
    <template v-if="canAlign">
      <div class="control-divider"></div>
      <button @click="$emit('align-left')" class="control-btn" title="Align Left">
        <AlignStartVertical :size="16" />
      </button>
      <button @click="$emit('align-right')" class="control-btn" title="Align Right">
        <AlignEndVertical :size="16" />
      </button>
      <button @click="$emit('align-top')" class="control-btn" title="Align Top">
        <AlignStartHorizontal :size="16" />
      </button>
      <button @click="$emit('align-bottom')" class="control-btn" title="Align Bottom">
        <AlignEndHorizontal :size="16" />
      </button>
    </template>

    <!-- Distribution Tools (visible when 3+ nodes selected) -->
    <template v-if="canDistribute">
      <div class="control-divider"></div>
      <button @click="$emit('distribute-h')" class="control-btn" title="Distribute Horizontally">
        <AlignHorizontalDistributeCenter :size="16" />
      </button>
      <button @click="$emit('distribute-v')" class="control-btn" title="Distribute Vertically">
        <AlignVerticalDistributeCenter :size="16" />
      </button>
    </template>

  </div>
</template>

<script setup>
import {
  LayoutGrid, ZoomIn, ZoomOut, Maximize2,
  AlignStartVertical, AlignEndVertical, AlignStartHorizontal, AlignEndHorizontal,
  AlignHorizontalDistributeCenter, AlignVerticalDistributeCenter
} from 'lucide-vue-next'

defineProps({
  canAlign: { type: Boolean, default: false },
  canDistribute: { type: Boolean, default: false }
})

defineEmits([
  'zoom-in', 'zoom-out', 'fit-view', 'auto-layout',
  'align-left', 'align-right', 'align-top', 'align-bottom',
  'distribute-h', 'distribute-v'
])
</script>

<style scoped>
.canvas-controls {
  position: absolute;
  left: 10px;
  bottom: 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: rgba(30, 41, 59, 0.95);
  border: 1px solid #374151;
  border-radius: 8px;
  padding: 4px;
  z-index: 5;
}

.control-btn {
  width: 28px;
  height: 28px;
  background: transparent;
  border: none;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #9CA3AF;
  transition: all 0.2s ease;
}

.control-btn:hover {
  background: rgba(139, 92, 246, 0.2);
  color: #8B5CF6;
}

.control-btn.active {
  background: rgba(139, 92, 246, 0.3);
  color: #A78BFA;
}

.control-divider {
  height: 1px;
  background: #374151;
  margin: 4px 2px;
}

</style>
