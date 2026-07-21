<template>
  <div class="w-full h-full bg-[#0a0a0f] overflow-auto">
    <!-- Background Grid Pattern -->
    <div class="absolute inset-0 opacity-[0.03] pointer-events-none" style="background-image: linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px); background-size: 20px 20px;" />

    <!-- No Data State -->
    <div v-if="allNodes.length === 0" class="relative flex items-center justify-center h-full">
      <div class="text-center">
        <div class="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center border border-gray-700/50 shadow-2xl">
          <svg class="w-10 h-10 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
        </div>
        <p class="text-sm font-medium text-gray-400">{{ $t('debug.lineage.noExecutionData') }}</p>
        <p class="text-xs text-gray-600 mt-1">{{ $t('debug.lineage.runWorkflowHint') }}</p>
      </div>
    </div>

    <!-- Pipeline View -->
    <div v-else class="relative p-6">
      <div class="max-w-xl mx-auto">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <div class="relative">
            <div class="w-3 h-3 rounded-full bg-emerald-500" />
            <div class="absolute inset-0 w-3 h-3 rounded-full bg-emerald-500 animate-ping opacity-75" />
          </div>
          <span class="text-sm font-semibold text-gray-300 tracking-wide">{{ $t('debug.lineage.executionTrace').toUpperCase() }}</span>
          <div class="flex-1 h-px bg-gradient-to-r from-gray-700 to-transparent" />
          <span class="text-xs text-gray-500 tabular-nums">{{ allNodes.length }} {{ $t('debug.lineage.steps') }}</span>
        </div>

        <!-- Steps -->
        <div class="space-y-3">
          <div
            v-for="(node, index) in allNodes"
            :key="node.id"
            class="group"
          >
            <!-- Step Card -->
            <div
              :class="[
                'relative rounded-xl border transition-all duration-300 cursor-pointer overflow-hidden',
                node.status === 'failed'
                  ? 'bg-gradient-to-r from-red-950/50 to-red-900/20 border-red-500/40 shadow-lg shadow-red-500/10'
                  : node.id === focusedNodeId
                    ? 'bg-gradient-to-r from-violet-950/50 to-purple-900/20 border-violet-500/40 shadow-lg shadow-violet-500/10'
                    : 'bg-gradient-to-r from-gray-900/80 to-gray-800/40 border-gray-700/40 hover:border-gray-600/60 hover:shadow-lg hover:shadow-gray-900/50'
              ]"
              @click="handleNodeClick(node)"
            >
              <!-- Glow Effect -->
              <div
                v-if="node.status === 'failed'"
                class="absolute inset-0 bg-gradient-to-r from-red-500/5 to-transparent pointer-events-none"
              />
              <div
                v-else-if="node.id === focusedNodeId"
                class="absolute inset-0 bg-gradient-to-r from-violet-500/5 to-transparent pointer-events-none"
              />

              <!-- Main Content -->
              <div class="relative flex items-center gap-4 p-4">
                <!-- Step Indicator -->
                <div class="relative flex-shrink-0">
                  <div
                    :class="[
                      'w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold border',
                      node.status === 'failed'
                        ? 'bg-red-500/20 border-red-500/50 text-red-400'
                        : node.lane === 'source'
                          ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                          : node.lane === 'sink'
                            ? 'bg-orange-500/20 border-orange-500/50 text-orange-400'
                            : 'bg-blue-500/20 border-blue-500/50 text-blue-400'
                    ]"
                  >
                    <span v-if="node.status === 'failed'" class="text-lg">×</span>
                    <span v-else>{{ index + 1 }}</span>
                  </div>
                  <!-- Connector Line -->
                  <div
                    v-if="index < allNodes.length - 1"
                    class="absolute left-1/2 top-full w-px h-3 -translate-x-1/2 bg-gradient-to-b from-gray-600 to-gray-700"
                  />
                </div>

                <!-- Info -->
                <div class="flex-1 min-w-0 space-y-1">
                  <div class="flex items-center gap-2">
                    <span class="font-semibold text-white truncate">{{ node.stepId }}</span>
                    <span
                      v-if="node.loopCount > 1"
                      class="px-1.5 py-0.5 text-[10px] font-bold bg-violet-500/20 text-violet-300 rounded-md border border-violet-500/30"
                    >×{{ node.loopCount }}</span>
                  </div>
                  <div class="flex items-center gap-2 text-xs text-gray-500">
                    <code class="font-mono">{{ node.moduleId }}</code>
                  </div>
                </div>

                <!-- Lane Badge -->
                <div
                  :class="[
                    'px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded-lg flex-shrink-0',
                    node.lane === 'source'
                      ? 'bg-emerald-950/50 text-emerald-400 border border-emerald-500/30'
                      : node.lane === 'sink'
                        ? 'bg-orange-950/50 text-orange-400 border border-orange-500/30'
                        : 'bg-blue-950/50 text-blue-400 border border-blue-500/30'
                  ]"
                >{{ node.lane }}</div>

                <!-- Chevron -->
                <svg
                  :class="[
                    'w-5 h-5 flex-shrink-0 transition-all duration-300',
                    node.id === focusedNodeId
                      ? 'rotate-90 text-violet-400'
                      : 'text-gray-600 group-hover:text-gray-400 group-hover:translate-x-0.5'
                  ]"
                  viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                >
                  <path d="M9 18l6-6-6-6"/>
                </svg>
              </div>

              <!-- Expanded Panel -->
              <div
                v-if="node.id === focusedNodeId || node.status === 'failed'"
                class="relative border-t border-gray-700/30 bg-black/20"
              >
                <div class="p-4 space-y-3">
                  <!-- Inputs -->
                  <div v-if="node.consumedVariables?.length">
                    <div class="flex items-center gap-2 mb-2">
                      <div class="w-1.5 h-1.5 rounded-full bg-amber-400" />
                      <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{{ $t('debug.lineage.inputs') }}</span>
                    </div>
                    <div class="flex flex-wrap gap-2">
                      <div
                        v-for="varName in node.consumedVariables.slice(0, 8)"
                        :key="varName"
                        class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-800/80 rounded-lg border border-gray-700/50 text-xs"
                      >
                        <svg class="w-3 h-3 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M19 12H5M12 19l-7-7 7-7"/>
                        </svg>
                        <code class="text-gray-300">{{ varName }}</code>
                      </div>
                      <span v-if="node.consumedVariables.length > 8" class="text-xs text-gray-500 self-center">
                        {{ $t('debug.lineage.more', { count: node.consumedVariables.length - 8 }) }}
                      </span>
                    </div>
                  </div>

                  <!-- Outputs -->
                  <div v-if="node.producedVariables?.length">
                    <div class="flex items-center gap-2 mb-2">
                      <div class="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{{ $t('debug.lineage.outputs') }}</span>
                    </div>
                    <div class="flex flex-wrap gap-2">
                      <code
                        v-for="varName in node.producedVariables.slice(0, 8)"
                        :key="varName"
                        class="px-2.5 py-1 bg-emerald-950/50 text-emerald-300 rounded-lg border border-emerald-500/20 text-xs"
                      >{{ varName }}</code>
                      <span v-if="node.producedVariables.length > 8" class="text-xs text-gray-500 self-center">
                        {{ $t('debug.lineage.more', { count: node.producedVariables.length - 8 }) }}
                      </span>
                    </div>
                  </div>

                  <!-- No Dependencies -->
                  <div
                    v-if="!node.consumedVariables?.length && !node.producedVariables?.length"
                    class="text-xs text-gray-500 italic"
                  >
                    {{ $t('debug.lineage.noVariableDeps') }}
                  </div>

                  <!-- Error -->
                  <div v-if="node.status === 'failed' && node.error" class="pt-2">
                    <div class="flex items-center gap-2 mb-2">
                      <div class="w-1.5 h-1.5 rounded-full bg-red-400" />
                      <span class="text-[10px] font-bold text-red-400 uppercase tracking-widest">{{ $t('debug.error') }}</span>
                    </div>
                    <div class="px-3 py-2 bg-red-950/30 rounded-lg border border-red-500/20">
                      <code class="text-xs text-red-300 font-mono">{{ node.error }}</code>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="mt-6 flex items-center justify-center gap-6 text-[10px] text-gray-600">
          <div class="flex items-center gap-1.5">
            <div class="w-2 h-2 rounded bg-emerald-500/50" />
            <span>{{ $t('debug.lineage.source') }}</span>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-2 h-2 rounded bg-blue-500/50" />
            <span>{{ $t('debug.lineage.transform') }}</span>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-2 h-2 rounded bg-orange-500/50" />
            <span>{{ $t('debug.lineage.sink') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  sources: { type: Array, default: () => [] },
  transforms: { type: Array, default: () => [] },
  sinks: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  groups: { type: Array, default: () => [] },
  viewMode: { type: String, default: 'lineage' },
  focusedNodeId: { type: String, default: null },
  focusedUpstream: { type: Array, default: () => [] },
  focusedDownstream: { type: Array, default: () => [] },
  highlightedEdges: { type: Array, default: () => [] }
})

const emit = defineEmits(['node-click', 'view-change', 'clear-focus'])

const allNodes = computed(() => {
  const nodes = [...props.sources, ...props.transforms, ...props.sinks]
  return nodes.sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
})

function handleNodeClick(node) {
  emit('node-click', node)
}
</script>
