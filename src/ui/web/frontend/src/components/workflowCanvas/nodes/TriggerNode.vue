<template>
  <div class="trigger-node shape-semicircle" :class="nodeClasses">
    <!-- Delete button -->
    <button
      @click.stop="$emit('delete-node', { nodeId: id })"
      aria-label="Delete node"
      class="delete-btn"
    >
      <X :size="14" />
    </button>

    <!-- Semicircle card -->
    <div class="trigger-card">
      <div class="trigger-content">
        <component :is="triggerIcon" :size="20" class="trigger-icon" />
        <div class="trigger-info">
          <span class="trigger-label">{{ label }}</span>
          <span class="trigger-type">{{ triggerTypeLabel }}</span>
        </div>
      </div>
    </div>

    <!-- Source handle (output) -->
    <Handle
      id="output"
      type="source"
      :position="Position.Right"
      class="handle handle-source"
    />

    <!-- Add button -->
    <button
      v-if="showAddButton"
      @click.stop="$emit('add-node', { nodeId: id, sourceHandle: 'output' })"
      aria-label="Add node"
      class="add-btn"
    >
      <Plus :size="16" />
    </button>

    <!-- Test Trigger button (webhook only) -->
    <button
      v-if="isWebhook && selected"
      @click.stop="showTestPanel = true"
      class="test-trigger-btn"
      :title="$t('triggers.webhookTest', 'Test Webhook')"
    >
      <Play :size="12" />
    </button>

    <!-- Category badge -->
    <div class="category-badge">
      {{ $t('node.trigger.badge', 'TRIGGER') }}
    </div>

    <!-- Webhook Test Panel (floating) -->
    <Teleport to="body">
      <div
        v-if="showTestPanel && data?.linkedWebhookId"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30"
        @click.self="showTestPanel = false"
      >
        <WebhookTestPanel
          :webhook-id="data.linkedWebhookId"
          @close="showTestPanel = false"
        />
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import { Plus, X, Zap, Clock, Webhook, Hand, Radio, Play } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import WebhookTestPanel from '@/components/triggers/WebhookTestPanel.vue'

const { t } = useI18n()

const props = defineProps({
  id: String,
  data: Object,
  selected: Boolean,
  isFirst: Boolean,
  hasForwardEdge: Boolean,
  showAddButton: Boolean,
  hasCheckpoint: Boolean,
  label: String,
  triggerType: { type: String, default: 'manual' },
  executionState: String,
  disabled: { type: Boolean, default: false }
})

defineEmits(['add-node', 'delete-node'])

const showTestPanel = ref(false)

const isWebhook = computed(() => {
  const type = props.data?.params?.trigger_type || props.triggerType
  return type === 'webhook'
})

// Trigger type to icon mapping
const triggerIcon = computed(() => {
  const type = props.data?.params?.trigger_type || props.triggerType
  const icons = {
    manual: Hand,
    webhook: Webhook,
    schedule: Clock,
    event: Radio
  }
  return icons[type] || Zap
})

// Trigger type label
const triggerTypeLabel = computed(() => {
  const type = props.data?.params?.trigger_type || props.triggerType
  return t(`node.trigger.types.${type}`, type)
})

const nodeClasses = computed(() => ({
  'selected': props.selected,
  'dimmed': props.data?.dimmed,
  'highlighted': props.data?.highlighted,
  'debug-selected': props.data?.debugSelected,
  'has-checkpoint': props.hasCheckpoint,
  'execution-running': props.executionState === 'running',
  'execution-completed': props.executionState === 'completed',
  'execution-pending': props.executionState === 'pending',
  'node-disabled': props.disabled
}))
</script>

<style scoped>
@import '@/styles/nodeDesignSystem.css';
@import '@/styles/nodeShapeEffects.css';

/* Semicircle trigger node: dimensions from backend SSOT */
.trigger-node {
  position: relative;
  width: var(--node-trigger-width, 120px);
  height: var(--node-trigger-height, 76px);
  transition: transform 0.2s ease;

  /* Shape CSS variables (semicircle: left rounded, right flat) */
  --shape-border-radius: 38px 0 0 38px;
  --shape-outer-radius: 40px 0 0 40px;
}

.trigger-node:hover {
  transform: translateY(-2px);
}

/* Semicircle card (uses CSS variable from shape class) */
.trigger-card {
  width: 100%;
  height: 100%;
  border-radius: var(--shape-border-radius, 38px 0 0 38px);
  background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
  border: 2px solid #D97706;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
  transition: all 0.2s ease;
  position: relative;
  z-index: 1;
}

.trigger-node:hover .trigger-card {
  border-color: #FBBF24;
  box-shadow: 0 8px 24px rgba(245, 158, 11, 0.5);
}

/* Content layout */
.trigger-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding-left: 8px;  /* Offset for semicircle curve */
}

.trigger-icon {
  color: white;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

.trigger-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
}

.trigger-label {
  font-size: 11px;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trigger-type {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.8);
  text-transform: capitalize;
}

/* Selected state - glow effect (better for semicircle shape) */
.trigger-node.selected .trigger-card {
  border-color: #FBBF24;
  box-shadow:
    0 0 0 2px #F59E0B,
    0 0 20px rgba(245, 158, 11, 0.6),
    0 0 40px rgba(245, 158, 11, 0.3);
  animation: trigger-glow 1.5s ease-in-out infinite;
}

@keyframes trigger-glow {
  0%, 100% {
    box-shadow:
      0 0 0 2px #F59E0B,
      0 0 20px rgba(245, 158, 11, 0.6),
      0 0 40px rgba(245, 158, 11, 0.3);
  }
  50% {
    box-shadow:
      0 0 0 3px #FBBF24,
      0 0 30px rgba(245, 158, 11, 0.8),
      0 0 60px rgba(245, 158, 11, 0.4);
  }
}

/* Handle - at flat edge (right side) */
.handle {
  width: 12px !important;
  height: 12px !important;
  border: 2px solid #374151 !important;
  background: #6B7280 !important;
  transition: all 0.2s ease;
  top: 50% !important;
  right: -6px !important;
  transform: translateY(-50%) !important;
}

.trigger-node:hover .handle {
  border-color: #F59E0B;
  transform: translateY(-50%) scale(1.2) !important;
}

/* Delete button - top left */
.delete-btn {
  position: absolute;
  top: -8px;
  left: 8px;  /* Adjusted for semicircle */
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #EF4444;
  border: 2px solid #1F2937;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 20;
  color: white;
}

.trigger-node:hover .delete-btn { opacity: 1; }
.delete-btn:hover { transform: scale(1.2); background: #DC2626; }

/* Add button - right side */
.add-btn {
  position: absolute;
  right: -20px;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
  border: 3px solid #1F2937;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 10;
  color: white;
}

.trigger-node:hover .add-btn { opacity: 1; }
.add-btn:hover { transform: translateY(-50%) scale(1.15); }

/* Category badge - top right (must be above glow effects) */
.category-badge {
  position: absolute;
  top: -8px;
  right: 4px;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 8px;
  font-weight: 700;
  text-transform: uppercase;
  color: #D97706;
  background: #FEF3C7;
  border: 1px solid #F59E0B;
  z-index: 15;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* Test Trigger button */
.test-trigger-btn {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
  border: 2px solid #1F2937;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 20;
  color: white;
  transition: all 0.2s ease;
}

.test-trigger-btn:hover {
  transform: translateX(-50%) scale(1.15);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.5);
}

/* States */
.trigger-node.dimmed { opacity: 0.4; pointer-events: none; }

.trigger-node.execution-running .trigger-card {
  animation: running-pulse 1.5s ease-in-out infinite;
}

.trigger-node.execution-completed .trigger-card {
  border-color: #10B981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3);
}

/* Checkpoint state - pulsing red glow (better for semicircle) */
.trigger-node.has-checkpoint .trigger-card {
  border-color: #EF4444;
  animation: checkpoint-pulse 1.5s ease-in-out infinite;
}

@keyframes checkpoint-pulse {
  0%, 100% {
    box-shadow:
      0 0 0 2px #EF4444,
      0 0 15px rgba(239, 68, 68, 0.5);
  }
  50% {
    box-shadow:
      0 0 0 4px #EF4444,
      0 0 30px rgba(239, 68, 68, 0.7),
      0 0 50px rgba(239, 68, 68, 0.3);
  }
}

@keyframes running-pulse {
  0%, 100% { box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.3); }
  50% { box-shadow: 0 0 0 6px rgba(245, 158, 11, 0.4); }
}

/* ========== Disabled State ========== */
.trigger-node.node-disabled {
  cursor: not-allowed;
}

.trigger-node.node-disabled:hover {
  transform: none;
}

.trigger-node.node-disabled:hover .trigger-card {
  border-color: #F97316;
  box-shadow: 0 0 12px rgba(249, 115, 22, 0.3);
}

.trigger-node.node-disabled .handle {
  opacity: 0.4;
}

.trigger-node.node-disabled .add-btn {
  display: none;
}

.trigger-node.node-disabled .category-badge {
  filter: grayscale(70%);
  opacity: 0.5;
}
</style>
