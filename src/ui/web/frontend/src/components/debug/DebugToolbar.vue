<template>
  <div class="debug-dock" @click.stop>
    <button
      v-for="(tool, i) in availableTools"
      :key="tool.id"
      @click="$emit(`toggle-${tool.id}`)"
      :disabled="tool.disabled"
      class="dock-item"
      :class="{ active: activePanel === tool.id, disabled: tool.disabled }"
      :style="{ '--c': tool.rgb, '--i': i }"
      :aria-label="tool.label"
    >
      <div class="dock-icon">
        <component :is="tool.icon" :size="18" />
      </div>
      <span class="dock-tip">{{ tool.label }}</span>
      <!-- Badge -->
      <span v-if="tool.badge" class="dock-badge">{{ tool.badge }}</span>
      <!-- Test status dot -->
      <span v-if="tool.dot" class="dock-dot" :class="tool.dot" />
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useCapabilitiesStore } from '@/stores/capabilitiesStore'
import { storeToRefs } from 'pinia'
import {
  Camera,
  GitBranch,
  RotateCcw,
  FlaskConical,
  History,
  Clock,
  Timer
} from 'lucide-vue-next'

const { t } = useI18n()
const capsStore = useCapabilitiesStore()
const { hasEvidence, hasLineage, hasReplay, hasTests, hasVersions } = storeToRefs(capsStore)

const props = defineProps({
  activePanel: {
    type: String,
    default: null,
    validator: (v) => v === null || ['evidence', 'lineage', 'replay', 'history', 'timeline', 'tests', 'versions'].includes(v)
  },
  canReplay: {
    type: Boolean,
    default: true
  },
  hasTimeline: {
    type: Boolean,
    default: false
  },
  testStatus: {
    type: String,
    default: null,
    validator: (v) => v === null || ['passed', 'failed', 'running'].includes(v)
  },
  lockedCount: {
    type: Number,
    default: 0
  },
  executionCount: {
    type: Number,
    default: 0
  }
})

defineEmits([
  'toggle-evidence',
  'toggle-lineage',
  'toggle-replay',
  'toggle-history',
  'toggle-timeline',
  'toggle-tests',
  'toggle-versions'
])

// Only show tools the user has access to — no locked state
const availableTools = computed(() => {
  const tools = []

  if (hasEvidence.value) {
    tools.push({
      id: 'evidence',
      icon: Camera,
      label: t('debug.toolbar.evidence'),
      rgb: '59, 130, 246',
    })
  }

  if (hasLineage.value) {
    tools.push({
      id: 'lineage',
      icon: GitBranch,
      label: t('debug.toolbar.lineage'),
      rgb: '139, 92, 246',
    })
  }

  if (hasReplay.value) {
    tools.push({
      id: 'history',
      icon: Clock,
      label: t('debug.toolbar.history'),
      rgb: '34, 197, 94',
      badge: props.executionCount > 0 ? props.executionCount : null,
    })
  }

  if (props.hasTimeline) {
    tools.push({
      id: 'timeline',
      icon: Timer,
      label: t('debug.toolbar.timeline', 'Timeline'),
      rgb: '16, 185, 129',
    })
  }

  if (hasReplay.value) {
    tools.push({
      id: 'replay',
      icon: RotateCcw,
      label: t('debug.toolbar.replay'),
      rgb: '124, 58, 237',
      disabled: !props.canReplay,
    })
  }

  if (hasTests.value) {
    tools.push({
      id: 'tests',
      icon: FlaskConical,
      label: t('debug.toolbar.tests'),
      rgb: '245, 158, 11',
      dot: props.testStatus === 'passed' ? 'dot-green'
        : props.testStatus === 'failed' ? 'dot-red'
        : props.testStatus === 'running' ? 'dot-yellow'
        : null,
    })
  }

  if (hasVersions.value) {
    tools.push({
      id: 'versions',
      icon: History,
      label: t('debug.toolbar.versions'),
      rgb: '6, 182, 212',
      badge: props.lockedCount > 0 ? props.lockedCount : null,
    })
  }

  return tools
})
</script>

<style scoped>
.debug-dock {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 14px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.03) inset;
}

/* Each icon button */
.dock-item {
  position: relative;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  color: rgba(148, 163, 184, 0.7);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  animation: dock-pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: calc(var(--i) * 40ms);
}

@keyframes dock-pop {
  from {
    opacity: 0;
    transform: scale(0.5) translateY(8px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.dock-item .dock-icon {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease;
}

/* Hover state — glow up */
.dock-item:hover:not(.disabled) {
  color: rgb(var(--c));
  background: rgba(var(--c), 0.1);
  border-color: rgba(var(--c), 0.2);
  box-shadow: 0 0 20px rgba(var(--c), 0.15);
  transform: translateY(-2px);
}

.dock-item:hover:not(.disabled) .dock-icon {
  transform: scale(1.15);
}

/* Active state — bright ring */
.dock-item.active {
  color: rgb(var(--c));
  background: rgba(var(--c), 0.15);
  border-color: rgba(var(--c), 0.4);
  box-shadow:
    0 0 20px rgba(var(--c), 0.2),
    0 0 0 1px rgba(var(--c), 0.1) inset;
}

.dock-item.active::after {
  content: '';
  position: absolute;
  bottom: 2px;
  left: 50%;
  transform: translateX(-50%);
  width: 12px;
  height: 2px;
  border-radius: 1px;
  background: rgb(var(--c));
  box-shadow: 0 0 6px rgba(var(--c), 0.6);
}

/* Disabled state */
.dock-item.disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* Tooltip */
.dock-tip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%) translateY(4px);
  padding: 4px 10px;
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 6px;
  color: #e2e8f0;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transition: all 0.15s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.dock-tip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 4px solid transparent;
  border-top-color: rgba(71, 85, 105, 0.5);
}

.dock-item:hover .dock-tip {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

/* Badge (count) */
.dock-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(var(--c), 0.9);
  border-radius: 8px;
  font-size: 9px;
  font-weight: 700;
  color: white;
  padding: 0 4px;
  pointer-events: none;
  box-shadow: 0 0 8px rgba(var(--c), 0.4);
}

/* Status dot (test result) */
.dock-dot {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  pointer-events: none;
  box-shadow: 0 0 6px currentColor;
}

.dock-dot.dot-green {
  background: #22c55e;
  color: #22c55e;
}

.dock-dot.dot-red {
  background: #ef4444;
  color: #ef4444;
}

.dock-dot.dot-yellow {
  background: #eab308;
  color: #eab308;
  animation: pulse-dot 1.5s ease infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
