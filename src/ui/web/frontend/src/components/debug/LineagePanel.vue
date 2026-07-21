<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-x-full"
      enter-to-class="opacity-100 translate-x-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-x-0"
      leave-to-class="opacity-0 translate-x-full"
    >
      <div
        v-if="isOpen"
        class="fixed top-0 right-0 h-full w-[700px] bg-gray-900 border-l border-gray-700 shadow-2xl z-40 flex flex-col"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-purple-900/20">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-purple-600/20 rounded-lg">
              <GitBranch :size="20" class="text-purple-400" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-white">{{ $t('debug.lineage.title') }}</h3>
              <p class="text-xs text-gray-400">
                {{ nodeCount }} {{ $t('debug.lineage.nodes') }} · {{ edgeCount }} {{ $t('debug.lineage.edges') }}
              </p>
            </div>
          </div>
          <button
            @click="$emit('close')"
            class="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
            aria-label="Close"
          >
            <X :size="20" />
          </button>
        </div>

        <!-- Loading -->
        <div v-if="isLoading && !hasData" class="flex-1 flex items-center justify-center">
          <Loader :size="32" class="text-purple-400 animate-spin" />
        </div>

        <!-- Graph View -->
        <div v-else-if="hasData" class="flex-1 overflow-hidden relative">
          <LineageGraph
            :sources="swimlane.sources"
            :transforms="swimlane.transforms"
            :sinks="swimlane.sinks"
            :edges="swimlane.dataEdges"
            :groups="swimlane.groups"
            :view-mode="viewMode"
            :focused-node-id="focusedNode"
            :focused-upstream="focusData?.upstream || []"
            :focused-downstream="focusData?.downstream || []"
            :highlighted-edges="focusData?.highlightEdges || []"
            @node-click="handleNodeClick"
            @view-change="handleViewChange"
            @clear-focus="clearFocus"
          />
        </div>

        <!-- No Execution ID -->
        <div v-else-if="!executionId" class="flex-1 flex flex-col items-center justify-center text-gray-400">
          <Play :size="48" class="mb-3 opacity-50" />
          <p class="text-sm font-medium">{{ $t('debug.lineage.runWorkflowFirst', 'Run workflow first') }}</p>
          <p class="text-xs mt-2 text-gray-500">{{ $t('debug.lineage.runFirstHint', 'Execute the workflow to see data lineage') }}</p>
        </div>

        <!-- Empty State -->
        <div v-else class="flex-1 flex flex-col items-center justify-center text-gray-400">
          <GitBranch :size="48" class="mb-3 opacity-50" />
          <p class="text-sm">{{ $t('debug.lineage.noData') }}</p>
          <button
            @click="handleRefresh"
            class="mt-3 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg transition-colors"
            aria-label="Load graph"
          >
            {{ $t('debug.lineage.loadGraph') }}
          </button>
        </div>

        <!-- Node Detail Panel (Evidence Panel) -->
        <Transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="opacity-0 translate-y-4"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 translate-y-4"
        >
          <div
            v-if="selectedNode"
            class="border-t border-gray-700 bg-gray-800/80 backdrop-blur max-h-80 overflow-auto"
          >
            <div class="p-4">
              <!-- Header -->
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div
                    class="w-8 h-8 rounded-lg flex items-center justify-center"
                    :style="{ backgroundColor: getCategoryColor(selectedNode.category) + '30' }"
                  >
                    <component
                      :is="getCategoryIcon(selectedNode.category)"
                      :size="16"
                      :style="{ color: getCategoryColor(selectedNode.category) }"
                    />
                  </div>
                  <div>
                    <h4 class="text-sm font-semibold text-white">
                      {{ selectedNode.label || selectedNode.stepId }}
                    </h4>
                    <p class="text-xs text-gray-400 font-mono">{{ selectedNode.moduleId }}</p>
                  </div>
                </div>
                <button
                  @click="selectedNode = null"
                  class="p-1 text-gray-400 hover:text-white rounded"
                  aria-label="Close"
                >
                  <X :size="16" />
                </button>
              </div>

              <!-- Data Flow Summary -->
              <div class="grid grid-cols-2 gap-3 mb-4">
                <!-- Inputs (Consumed) -->
                <div class="bg-gray-900/50 rounded-lg p-3">
                  <div class="flex items-center gap-2 mb-2">
                    <ArrowDownLeft :size="14" class="text-amber-400" />
                    <span class="text-xs font-medium text-gray-300">{{ $t('debug.lineage.inputs') }}</span>
                  </div>
                  <div class="space-y-1">
                    <div
                      v-for="varName in (selectedNode.consumedVariables || []).slice(0, 5)"
                      :key="varName"
                      class="text-xs font-mono text-gray-400 truncate"
                    >
                      {{ varName }}
                    </div>
                    <div v-if="!selectedNode.consumedVariables?.length" class="text-xs text-gray-500 italic">
                      {{ $t('debug.lineage.noInputs') }}
                    </div>
                    <div
                      v-if="(selectedNode.consumedVariables?.length || 0) > 5"
                      class="text-xs text-gray-500"
                    >
                      {{ $t('debug.lineage.more', { count: selectedNode.consumedVariables.length - 5 }) }}
                    </div>
                  </div>
                </div>

                <!-- Outputs (Produced) -->
                <div class="bg-gray-900/50 rounded-lg p-3">
                  <div class="flex items-center gap-2 mb-2">
                    <ArrowUpRight :size="14" class="text-green-400" />
                    <span class="text-xs font-medium text-gray-300">{{ $t('debug.lineage.outputs') }}</span>
                  </div>
                  <div class="space-y-1">
                    <div
                      v-for="varName in (selectedNode.producedVariables || []).slice(0, 5)"
                      :key="varName"
                      class="text-xs font-mono text-gray-400 truncate"
                    >
                      {{ varName }}
                    </div>
                    <div v-if="!selectedNode.producedVariables?.length" class="text-xs text-gray-500 italic">
                      {{ $t('debug.lineage.noOutputs') }}
                    </div>
                    <div
                      v-if="(selectedNode.producedVariables?.length || 0) > 5"
                      class="text-xs text-gray-500"
                    >
                      {{ $t('debug.lineage.more', { count: selectedNode.producedVariables.length - 5 }) }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Upstream/Downstream -->
              <div class="flex items-center gap-4 text-xs">
                <div class="flex items-center gap-2">
                  <ChevronLeft :size="14" class="text-purple-400" />
                  <span class="text-gray-400">
                    {{ selectedNode.upstream?.length || 0 }} {{ $t('debug.lineage.upstream') }}
                  </span>
                </div>
                <div class="flex items-center gap-2">
                  <ChevronRight :size="14" class="text-purple-400" />
                  <span class="text-gray-400">
                    {{ selectedNode.downstream?.length || 0 }} {{ $t('debug.lineage.downstream') }}
                  </span>
                </div>
              </div>

              <!-- Item-Level Origin (like n8n's pairedItem) -->
              <div v-if="selectedItemOrigins?.items?.length" class="mt-4 border-t border-gray-700 pt-4">
                <div class="flex items-center gap-2 mb-3">
                  <Link :size="14" class="text-cyan-400" />
                  <span class="text-xs font-medium text-gray-300">{{ $t('debug.lineage.itemOrigins', 'Item Origins') }}</span>
                  <span class="text-xs text-gray-500">({{ selectedItemOrigins.items.length }} items)</span>
                </div>
                <div class="space-y-2 max-h-32 overflow-auto">
                  <div
                    v-for="item in selectedItemOrigins.items.slice(0, 10)"
                    :key="item.index"
                    class="flex items-center justify-between bg-gray-900/50 rounded px-2 py-1.5"
                  >
                    <div class="flex items-center gap-2">
                      <span class="text-xs text-gray-500 font-mono">[{{ item.index }}]</span>
                      <span class="text-xs text-gray-300 truncate max-w-[120px]">{{ item.valuePreview }}</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <ArrowLeftRight :size="12" class="text-gray-500" />
                      <span class="text-xs text-cyan-400 font-mono">{{ item.origin?.nodeId }}</span>
                    </div>
                  </div>
                  <div v-if="selectedItemOrigins.items.length > 10" class="text-xs text-gray-500 text-center">
                    {{ $t('common.moreItems', { count: selectedItemOrigins.items.length - 10 }) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  GitBranch,
  X,
  Loader,
  Play,
  ArrowDownLeft,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Globe,
  Database,
  Cpu,
  Zap,
  Box,
  Link,
  ArrowLeftRight
} from 'lucide-vue-next'
import { useLineage } from '@/composables/debug/useLineage'
import LineageGraph from './LineageGraph.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  executionId: {
    type: String,
    default: null
  },
  stepId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['close', 'node-selected'])

const { t } = useI18n()

const {
  viewMode,
  swimlane,
  focusedNode,
  focusData,
  selectedNode,
  selectedItemOrigins,
  isLoading,
  hasData,
  nodeCount,
  edgeCount,
  loadSwimlane,
  loadGraph,
  focusNode,
  clearFocus,
  setViewMode,
  loadStepItemOrigins
} = useLineage()

// Load data when panel opens
watch(() => props.isOpen, async (open) => {
  if (open && props.executionId) {
    await loadSwimlane(props.executionId)
  }
})

// Focus on step if provided
watch(() => props.stepId, async (stepId) => {
  if (stepId && props.executionId) {
    await focusNode(props.executionId, `step_${stepId}`)
  }
})

async function handleRefresh() {
  if (props.executionId) {
    if (viewMode.value === 'lineage') {
      await loadSwimlane(props.executionId)
    } else {
      await loadGraph(props.executionId)
    }
  }
}

async function handleViewChange(mode) {
  setViewMode(mode)
  if (props.executionId) {
    if (mode === 'lineage') {
      await loadSwimlane(props.executionId)
    } else {
      await loadGraph(props.executionId, true)
    }
  }
}

async function handleNodeClick(node) {
  if (props.executionId) {
    await focusNode(props.executionId, node.id)

    // Load item-level origins for the clicked node
    const stepId = node.stepId || node.id.replace('step_', '')
    await loadStepItemOrigins(props.executionId, stepId)

    emit('node-selected', node)
  }
}

function getCategoryColor(category) {
  switch (category) {
    case 'browser': return '#f59e0b'
    case 'data': return '#14b8a6'
    case 'ai': return '#a855f7'
    case 'http': return '#3b82f6'
    case 'flow': return '#ec4899'
    default: return '#6366f1'
  }
}

function getCategoryIcon(category) {
  switch (category) {
    case 'browser': return Globe
    case 'data': return Database
    case 'ai': return Cpu
    case 'http': return Zap
    default: return Box
  }
}
</script>
