<template>
  <div class="w-full h-full bg-[#0a0a0f] overflow-hidden flex flex-col">
    <!-- Layer Toggle Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-gray-900/50">
      <!-- Title -->
      <div class="flex items-center gap-3">
        <div class="relative">
          <div class="w-2.5 h-2.5 rounded-full bg-violet-500" />
          <div v-if="isRunning" class="absolute inset-0 w-2.5 h-2.5 rounded-full bg-violet-500 animate-ping" />
        </div>
        <span class="text-sm font-semibold text-gray-200">
          {{ $t('lineage.storyline.title') }}
        </span>
        <span class="text-xs text-gray-500 tabular-nums">
          {{ totalSteps }} {{ $t('lineage.steps') }}
        </span>
      </div>

      <!-- Layer Toggle -->
      <div class="flex items-center gap-1 p-1 bg-gray-800/50 rounded-lg">
        <button
          v-for="layer in layers"
          :key="layer.id"
          :class="[
            'px-3 py-1.5 text-xs font-medium rounded-md transition-all',
            currentLayer === layer.id
              ? 'bg-violet-600 text-white shadow-lg'
              : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
          ]"
          @click="setLayer(layer.id)"
        >
          {{ layer.label }}
        </button>
      </div>
    </div>

    <!-- Background Grid -->
    <div class="absolute inset-0 opacity-[0.02] pointer-events-none" style="background-image: linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px); background-size: 24px 24px;" />

    <!-- Swimlanes Container -->
    <div class="flex-1 overflow-auto">
      <div class="min-h-full p-6">
        <!-- Empty State -->
        <div v-if="!hasSteps" class="flex items-center justify-center h-full">
          <div class="text-center">
            <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center border border-gray-700/50">
              <GitBranch :size="28" class="text-gray-600" />
            </div>
            <p class="text-sm font-medium text-gray-400">{{ $t('lineage.storyline.noSteps') }}</p>
            <p class="text-xs text-gray-600 mt-1">{{ $t('lineage.storyline.runHint') }}</p>
          </div>
        </div>

        <!-- Storyline Layout (Default Layer) -->
        <div v-else-if="currentLayer === 'storyline'" class="space-y-6">
          <!-- Swimlane Headers -->
          <div class="flex gap-4 sticky top-0 z-10 bg-[#0a0a0f]/90 backdrop-blur-sm pb-4">
            <div
              v-for="category in visibleCategories"
              :key="category"
              class="flex-1 min-w-[200px]"
            >
              <div class="flex items-center gap-2 px-3 py-2 rounded-lg" :style="{ backgroundColor: getCategoryConfig(category).bgColor }">
                <component
                  :is="getCategoryIcon(category)"
                  :size="16"
                  :style="{ color: getCategoryConfig(category).color }"
                />
                <span class="text-xs font-semibold uppercase tracking-wider" :style="{ color: getCategoryConfig(category).color }">
                  {{ getCategoryConfig(category).label }}
                </span>
                <span class="text-xs text-gray-500">
                  ({{ getStepsForCategory(category).length }})
                </span>
              </div>
            </div>
          </div>

          <!-- Swimlane Rows -->
          <div class="flex gap-4">
            <div
              v-for="category in visibleCategories"
              :key="category"
              class="flex-1 min-w-[200px] space-y-3"
            >
              <!-- Steps in this category -->
              <template v-for="step in getStepsForCategory(category)" :key="step.id">
                <!-- Loop Container -->
                <LoopContainer
                  v-if="step.isLoop"
                  :loop-id="step.id"
                  :loop-label="step.name || step.id"
                  :iterations="step.iterations || []"
                  :default-collapsed="step.iterations?.length > 3"
                  @iteration-click="handleIterationClick"
                >
                  <!-- Nested steps within loop -->
                  <div class="p-3 space-y-2">
                    <StepCard
                      v-for="nested in step.nestedSteps || []"
                      :key="nested.id"
                      :step="nested"
                      :is-focused="focusedStepId === nested.id"
                      @click="handleStepClick(nested)"
                    />
                  </div>
                </LoopContainer>

                <!-- Decision Node (special rendering for decide category) -->
                <DecisionNode
                  v-else-if="category === 'decide' && step.decision"
                  :decision="step.decision"
                  :is-expanded="focusedStepId === step.id"
                  @click="handleStepClick(step)"
                  @view-artifact="$emit('view-artifact', $event)"
                />

                <!-- Regular Step Card -->
                <StepCard
                  v-else
                  :step="step"
                  :is-focused="focusedStepId === step.id"
                  :category="category"
                  @click="handleStepClick(step)"
                />
              </template>

              <!-- Empty Lane -->
              <div
                v-if="getStepsForCategory(category).length === 0"
                class="flex items-center justify-center h-24 border-2 border-dashed border-gray-800 rounded-xl"
              >
                <span class="text-xs text-gray-600">{{ $t('lineage.storyline.noStepsInLane') }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Artifacts Layer -->
        <div v-else-if="currentLayer === 'artifacts'" class="space-y-4">
          <div
            v-for="artifact in artifacts"
            :key="artifact.id"
            class="p-4 bg-gray-900/50 border border-gray-700/50 rounded-xl hover:border-gray-600 transition-colors cursor-pointer"
            @click="$emit('view-artifact', artifact.id)"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center" :style="{ backgroundColor: getArtifactColor(artifact.type) + '20' }">
                <component :is="getArtifactIcon(artifact.type)" :size="18" :style="{ color: getArtifactColor(artifact.type) }" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-white truncate">{{ artifact.name }}</p>
                <p class="text-xs text-gray-500">{{ artifact.type }} · {{ artifact.producedBy }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Debug Layer -->
        <div v-else-if="currentLayer === 'debug'" class="space-y-3">
          <div
            v-for="step in allSteps"
            :key="step.id"
            :class="[
              'p-4 border rounded-xl transition-all cursor-pointer',
              step.status === 'failed'
                ? 'bg-red-950/30 border-red-500/40'
                : 'bg-gray-900/50 border-gray-700/50 hover:border-gray-600'
            ]"
            @click="handleStepClick(step)"
          >
            <div class="flex items-center gap-3">
              <div class="text-xs text-gray-500 font-mono w-8">{{ step.order || '-' }}</div>
              <div
                class="w-8 h-8 rounded-lg flex items-center justify-center"
                :style="{ backgroundColor: getCategoryConfig(step.category).bgColor }"
              >
                <component
                  :is="getCategoryIcon(step.category)"
                  :size="14"
                  :style="{ color: getCategoryConfig(step.category).color }"
                />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-white truncate">{{ step.name || step.id }}</p>
                <p class="text-xs text-gray-500 font-mono truncate">{{ step.moduleId }}</p>
              </div>
              <span
                :class="[
                  'px-2 py-1 text-xs rounded',
                  step.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' :
                  step.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                  step.status === 'running' ? 'bg-blue-500/20 text-blue-400' :
                  'bg-gray-500/20 text-gray-400'
                ]"
              >
                {{ step.status }}
              </span>
              <span v-if="step.durationMs" class="text-xs text-gray-500 tabular-nums">
                {{ step.durationMs }}ms
              </span>
            </div>
            <!-- Error Display -->
            <div v-if="step.error" class="mt-3 px-3 py-2 bg-red-950/30 rounded-lg border border-red-500/20">
              <code class="text-xs text-red-300">{{ step.error }}</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  GitBranch,
  Eye,
  Calculator,
  Brain,
  Play,
  CheckCircle,
  Image,
  FileText,
  Code,
  Diff,
  Terminal
} from 'lucide-vue-next'
import { StepCategory, CATEGORY_ORDER, getCategoryConfig as getConfig } from './StepCategory'
import DecisionNode from './DecisionNode.vue'
import LoopContainer from './LoopContainer.vue'
import StepCard from './StepCard.vue'

const { t } = useI18n()

const props = defineProps({
  steps: {
    type: Array,
    default: () => []
  },
  artifacts: {
    type: Array,
    default: () => []
  },
  focusedStepId: {
    type: String,
    default: null
  },
  isRunning: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['step-click', 'iteration-click', 'view-artifact', 'layer-change'])

// Layers configuration
const layers = [
  { id: 'storyline', label: 'Storyline' },
  { id: 'artifacts', label: 'Artifacts' },
  { id: 'debug', label: 'Debug' }
]

const currentLayer = ref('storyline')

function setLayer(layerId) {
  currentLayer.value = layerId
  emit('layer-change', layerId)
}

// Computed
const hasSteps = computed(() => props.steps.length > 0)

const totalSteps = computed(() => props.steps.length)

const allSteps = computed(() => {
  return [...props.steps].sort((a, b) => (a.order || 0) - (b.order || 0))
})

const visibleCategories = computed(() => {
  // Only show categories that have steps
  return CATEGORY_ORDER.filter(cat =>
    props.steps.some(s => s.category === cat)
  )
})

// Category helpers
function getCategoryConfig(category) {
  return getConfig(category)
}

function getCategoryIcon(category) {
  const icons = {
    observe: Eye,
    evaluate: Calculator,
    decide: Brain,
    act: Play,
    verify: CheckCircle
  }
  return icons[category] || Play
}

function getStepsForCategory(category) {
  return props.steps.filter(s => s.category === category)
}

// Artifact helpers
function getArtifactIcon(type) {
  const icons = {
    screenshot: Image,
    report: FileText,
    decision: Brain,
    patch: Diff,
    diff: Diff,
    log: Terminal,
    data: Code
  }
  return icons[type] || FileText
}

function getArtifactColor(type) {
  const colors = {
    screenshot: '#3b82f6',
    report: '#f59e0b',
    decision: '#a855f7',
    patch: '#22c55e',
    diff: '#22c55e',
    log: '#6b7280',
    data: '#06b6d4'
  }
  return colors[type] || '#6b7280'
}

// Event handlers
function handleStepClick(step) {
  emit('step-click', step)
}

function handleIterationClick(iteration, index) {
  emit('iteration-click', { iteration, index })
}
</script>
