<template>
  <g
    class="glow-edge"
    :class="edgeClasses"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    @dblclick.stop="handleInsertClick"
  >
    <!-- Hit area for easier hover detection (invisible but wider) -->
    <path
      :d="path"
      class="edge-hit-area"
      fill="none"
      stroke="transparent"
      stroke-width="20"
    />

    <!-- Glow layer (background) - wider, blurred -->
    <path
      :d="path"
      class="edge-glow-layer"
      :style="glowStyle"
      fill="none"
    />

    <!-- Core layer (foreground) - crisp line -->
    <path
      :d="path"
      class="edge-core-layer vue-flow__edge-path"
      :style="coreStyle"
      fill="none"
      :marker-end="markerEnd"
    />

    <!-- Animated pulse particle (optional) -->
    <circle
      v-if="showPulse"
      :r="pulseRadius"
      class="edge-pulse-particle"
      :style="pulseStyle"
    >
      <animateMotion
        :dur="pulseDuration"
        repeatCount="indefinite"
        :path="path"
      />
    </circle>

    <!-- Insert Node Button (appears on hover) -->
    <EdgeLabelRenderer>
      <div
        v-show="isHovered || selected"
        :style="insertButtonStyle"
        class="edge-insert-button"
        @click.stop="handleInsertClick"
        @mouseenter="handleMouseEnter"
        @mouseleave="handleMouseLeave"
        :title="$t ? $t('workflow.insertNode') : 'Insert Node'"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
      </div>
    </EdgeLabelRenderer>

    <!-- Edge label (if provided) -->
    <EdgeLabelRenderer v-if="data?.label">
      <div
        :style="labelStyle"
        class="edge-label"
      >
        {{ data.label }}
      </div>
    </EdgeLabelRenderer>
  </g>
</template>

<script setup>
import { computed, ref, inject, onBeforeUnmount } from 'vue'
import { EdgeLabelRenderer, getBezierPath, getSmoothStepPath } from '@vue-flow/core'
import {
  EDGE_COLORS,
  EDGE_STYLE_PRESETS,
  getGlowFilterId
} from '@/config/edgeDesignSystem'

// Inject the insert handler from WorkflowCanvas
const onEdgeInsertNode = inject('onEdgeInsertNode', null)

// Hover state for showing insert button (with delay to prevent flicker)
const isHovered = ref(false)
let hoverTimeout = null

function handleMouseEnter() {
  if (hoverTimeout) clearTimeout(hoverTimeout)
  isHovered.value = true
}

function handleMouseLeave() {
  // Delay hiding to allow mouse to move to button
  hoverTimeout = setTimeout(() => {
    isHovered.value = false
  }, 150)
}

onBeforeUnmount(() => {
  if (hoverTimeout) clearTimeout(hoverTimeout)
})

const props = defineProps({
  id: { type: String, required: true },
  source: { type: String, required: true },
  target: { type: String, required: true },
  sourceX: { type: Number, required: true },
  sourceY: { type: Number, required: true },
  targetX: { type: Number, required: true },
  targetY: { type: Number, required: true },
  sourcePosition: { type: String, default: 'right' },
  targetPosition: { type: String, default: 'left' },
  sourceHandleId: { type: String, default: null },
  targetHandleId: { type: String, default: null },
  data: { type: Object, default: () => ({}) },
  markerEnd: { type: String, default: '' },
  style: { type: Object, default: () => ({}) },
  selected: { type: Boolean, default: false },
  // Custom props for glow edge
  edgeState: { type: String, default: 'idle' }, // idle, active, executing, completed, error
  colorType: { type: String, default: 'primary' }, // primary, success, error, warning, info
  pathType: { type: String, default: 'bezier' }, // bezier, smoothstep
  animated: { type: Boolean, default: false },
  showPulse: { type: Boolean, default: false }
})

// Calculate path based on type (check both props.pathType and data.pathType)
const path = computed(() => {
  const curvature = 0.25
  const pathTypeValue = props.pathType || props.data?.pathType || 'bezier'

  if (pathTypeValue === 'smoothstep') {
    const [pathData] = getSmoothStepPath({
      sourceX: props.sourceX,
      sourceY: props.sourceY,
      sourcePosition: props.sourcePosition,
      targetX: props.targetX,
      targetY: props.targetY,
      targetPosition: props.targetPosition,
      borderRadius: 16
    })
    return pathData
  }

  // Default: bezier
  const [pathData] = getBezierPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    sourcePosition: props.sourcePosition,
    targetX: props.targetX,
    targetY: props.targetY,
    targetPosition: props.targetPosition,
    curvature
  })
  return pathData
})

// Get color palette — custom color from data.edgeColor or style.stroke (fallback for saved edges)
const customColor = computed(() => {
  const fromData = props.data?.edgeColor
  if (fromData) return fromData
  // Fallback: style.stroke set at edge creation; treat any non-default color as custom
  const strokeColor = props.style?.stroke
  if (strokeColor && strokeColor !== EDGE_COLORS.primary.core) return strokeColor
  return null
})

const colors = computed(() => {
  if (customColor.value) {
    const c = customColor.value
    return { core: c, glow: `${c}99`, glowIntense: `${c}E6` }
  }
  return EDGE_COLORS[props.colorType] || EDGE_COLORS.primary
})

// Get style preset based on state
const stylePreset = computed(() => {
  const presetKey = props.edgeState === 'idle' ? 'default' : props.edgeState
  return EDGE_STYLE_PRESETS[presetKey] || EDGE_STYLE_PRESETS.default
})

// Edge classes for CSS styling
const edgeClasses = computed(() => ({
  'edge-selected': props.selected,
  'edge-animated': props.animated,
  [`edge-state-${props.edgeState}`]: true,
  [`edge-color-${props.colorType}`]: true
}))

// Glow layer style — never spread props.style (strokeWidth would kill glow)
const glowStyle = computed(() => {
  const preset = stylePreset.value
  const glowColor = props.selected ? colors.value.glowIntense : colors.value.glow
  // Custom color → use color-agnostic blur filter; otherwise use color-matrix filter
  const filterId = customColor.value ? 'edge-glow-intense' : getGlowFilterId(props.colorType)

  return {
    stroke: glowColor,
    strokeWidth: `${preset.glowWidth}px`,
    filter: `url(#${filterId})`,
    opacity: preset.glowOpacity
  }
})

// Core layer style — use colors.value.core (already includes custom color)
const coreStyle = computed(() => {
  const preset = stylePreset.value
  const dashStyle = props.animated && preset.dashArray
    ? {
        strokeDasharray: preset.dashArray,
        animation: `edge-flow ${preset.animationDuration || '1s'} linear infinite`
      }
    : {}

  return {
    stroke: colors.value.core,
    strokeWidth: `${preset.coreWidth}px`,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    filter: `drop-shadow(0 0 2px ${colors.value.glow})`,
    ...dashStyle
  }
})

// Pulse particle styling
const pulseRadius = computed(() => props.selected ? 4 : 3)
const pulseDuration = computed(() => '2s')
const pulseStyle = computed(() => ({
  fill: colors.value.core,
  filter: `url(#${getGlowFilterId(props.colorType)})`
}))

// Label positioning
const labelStyle = computed(() => {
  const midX = (props.sourceX + props.targetX) / 2
  const midY = (props.sourceY + props.targetY) / 2

  return {
    position: 'absolute',
    transform: `translate(-50%, -50%) translate(${midX}px, ${midY}px)`,
    pointerEvents: 'all'
  }
})

// Insert button positioning (at midpoint, offset from label if present)
const insertButtonStyle = computed(() => {
  const midX = (props.sourceX + props.targetX) / 2
  const midY = (props.sourceY + props.targetY) / 2
  // Offset slightly above center if there's a label
  const offsetY = props.data?.label ? -20 : 0

  return {
    position: 'absolute',
    transform: `translate(-50%, -50%) translate(${midX}px, ${midY + offsetY}px)`,
    pointerEvents: 'all'
  }
})

// Handle insert button click
function handleInsertClick(event) {
  event.stopPropagation()
  if (onEdgeInsertNode) {
    onEdgeInsertNode({
      edgeId: props.id,
      source: props.source,
      target: props.target,
      sourceHandleId: props.sourceHandleId,
      targetHandleId: props.targetHandleId,
      data: props.data,
      style: props.style
    })
  } else {
  }
}
</script>

<style>
/* Edge flow animation */
@keyframes edge-flow {
  from { stroke-dashoffset: 24; }
  to { stroke-dashoffset: 0; }
}

/* Reverse flow for error state */
@keyframes edge-flow-reverse {
  from { stroke-dashoffset: 0; }
  to { stroke-dashoffset: 18; }
}

/* Pulse glow animation */
@keyframes edge-glow-pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

.glow-edge {
  pointer-events: visibleStroke;
}

/* Invisible hit area for easier hover detection */
.glow-edge .edge-hit-area {
  pointer-events: stroke;
  cursor: pointer;
}

.glow-edge .edge-glow-layer {
  pointer-events: none;
  transition: opacity 0.3s ease, stroke-width 0.3s ease;
}

.glow-edge .edge-core-layer {
  cursor: pointer;
  transition: stroke-width 0.2s ease;
}

/* Hover state */
.glow-edge:hover .edge-glow-layer {
  opacity: 0.8;
  stroke-width: 16px;
}

.glow-edge:hover .edge-core-layer {
  stroke-width: 3px;
}

/* Selected state */
.glow-edge.edge-selected .edge-glow-layer {
  opacity: 0.9;
  stroke-width: 18px;
}

.glow-edge.edge-selected .edge-core-layer {
  stroke-width: 3px;
}

/* Animated state */
.glow-edge.edge-animated .edge-glow-layer {
  animation: edge-glow-pulse 2s ease-in-out infinite;
}

/* Error state - reverse animation */
.glow-edge.edge-state-error.edge-animated .edge-core-layer {
  animation: edge-flow-reverse 0.6s linear infinite;
}

/* Pulse particle */
.edge-pulse-particle {
  opacity: 0.9;
}

/* Edge label */
.edge-label {
  background: rgba(30, 41, 59, 0.9);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: #94A3B8;
  border: 1px solid rgba(139, 92, 246, 0.3);
  white-space: nowrap;
}

/* Insert node button */
.edge-insert-button {
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.4);
  transition: all 0.2s ease;
  z-index: 100;
  pointer-events: all !important;
}

.edge-insert-button:hover {
  transform: translate(-50%, -50%) scale(1.2);
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.6);
  background: linear-gradient(135deg, #A78BFA 0%, #818CF8 100%);
}

.edge-insert-button:active {
  transform: translate(-50%, -50%) scale(0.95);
}

.edge-insert-button svg {
  width: 14px;
  height: 14px;
}
</style>
