<template>
  <div
    class="checkpoint-marker"
    :class="{
      'enabled': checkpoint.enabled,
      'disabled': !checkpoint.enabled,
      'highlight': highlight
    }"
    :style="markerStyle"
    @click.stop="handleClick"
    @mouseenter="showTooltip = true"
    @mouseleave="showTooltip = false"
  >
    <div class="marker-dot">
      <CirclePause :size="14" />
    </div>

    <Transition name="fade">
      <div v-if="showTooltip" class="marker-tooltip">
        <div class="tooltip-title">{{ $t('checkpoint.humanCheckpoint') }}</div>
        <div class="tooltip-hint">
          {{ checkpoint.enabled ? $t('checkpoint.clickToRemove') : $t('checkpoint.disabled') }}
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { CirclePause } from 'lucide-vue-next'

const props = defineProps({
  checkpoint: {
    type: Object,
    required: true
    // { id, edge_id, enabled }
  },
  position: {
    type: Object,
    required: true
    // { x, y }
  },
  highlight: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'remove'])

const showTooltip = ref(false)

const markerStyle = computed(() => ({
  left: `${props.position.x}px`,
  top: `${props.position.y}px`
}))

function handleClick() {
  if (props.checkpoint.enabled) {
    emit('remove', props.checkpoint.id)
  } else {
    emit('click', props.checkpoint)
  }
}
</script>

<style scoped>
.checkpoint-marker {
  position: absolute;
  transform: translate(-50%, -50%);
  z-index: 100;
  cursor: pointer;
}

.marker-dot {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border: 2px solid #fca5a5;
  border-radius: 50%;
  color: white;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.5);
  transition: all 0.2s;
}

.checkpoint-marker:hover .marker-dot {
  transform: scale(1.15);
  box-shadow: 0 4px 16px rgba(239, 68, 68, 0.6);
}

.checkpoint-marker.disabled .marker-dot {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  border-color: #94a3b8;
  box-shadow: 0 2px 8px rgba(100, 116, 139, 0.3);
}

.checkpoint-marker.highlight .marker-dot {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 2px 8px rgba(239, 68, 68, 0.5);
  }
  50% {
    transform: scale(1.2);
    box-shadow: 0 4px 20px rgba(239, 68, 68, 0.8);
  }
}

.marker-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 8px;
  padding: 8px 12px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 8px;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  pointer-events: none;
}

.tooltip-title {
  font-size: 12px;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 2px;
}

.tooltip-hint {
  font-size: 10px;
  color: #94a3b8;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(4px);
}
</style>
