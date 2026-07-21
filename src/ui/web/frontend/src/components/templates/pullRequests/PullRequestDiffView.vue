<template>
  <div class="space-y-5 animate-fade-in">
    <!-- Section Header -->
    <div class="flex items-center justify-between">
      <h3 class="text-base font-semibold text-white">Changes</h3>
      <div v-if="totalChanges > 0" class="flex items-center gap-3 text-xs">
        <span v-if="addedSteps.length" class="flex items-center gap-1 text-emerald-400">
          <Plus :size="12" />
          {{ addedSteps.length }} added
        </span>
        <span v-if="removedSteps.length" class="flex items-center gap-1 text-red-400">
          <Minus :size="12" />
          {{ removedSteps.length }} removed
        </span>
        <span v-if="modifiedSteps.length" class="flex items-center gap-1 text-amber-400">
          <Pencil :size="12" />
          {{ modifiedSteps.length }} modified
        </span>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="totalChanges === 0" class="text-center py-12">
      <div class="w-12 h-12 rounded-full bg-gray-800/50 flex items-center justify-center mx-auto mb-3">
        <Pencil :size="20" class="text-gray-600" />
      </div>
      <p class="text-gray-400 text-sm">No changes detected</p>
    </div>

    <template v-else>
      <!-- Added Steps -->
      <DiffSection
        v-if="addedSteps.length"
        :label="`Added Steps (${addedSteps.length})`"
        color="emerald"
        :default-open="true"
      >
        <div class="space-y-3">
          <div
            v-for="step in addedSteps"
            :key="step.id"
            class="border-l-4 border-emerald-500 bg-gray-800/30 backdrop-blur rounded-xl p-4"
          >
            <div class="flex items-start gap-3">
              <div class="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Plus :size="14" class="text-emerald-400" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-white truncate">{{ step.label || step.id }}</p>
                <p v-if="step.module_id" class="text-xs text-gray-500 font-mono mt-0.5">{{ step.module_id }}</p>
              </div>
            </div>
          </div>
        </div>
      </DiffSection>

      <!-- Removed Steps -->
      <DiffSection
        v-if="removedSteps.length"
        :label="`Removed Steps (${removedSteps.length})`"
        color="red"
        :default-open="true"
      >
        <div class="space-y-3">
          <div
            v-for="stepId in diffSummary.removed_steps"
            :key="stepId"
            class="border-l-4 border-red-500 bg-gray-800/30 backdrop-blur rounded-xl p-4"
          >
            <div class="flex items-start gap-3">
              <div class="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Minus :size="14" class="text-red-400" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-red-300/80 truncate">{{ stepId }}</p>
                <p class="text-xs text-gray-600 mt-0.5">Step removed from workflow</p>
              </div>
            </div>
          </div>
        </div>
      </DiffSection>

      <!-- Modified Steps -->
      <DiffSection
        v-if="modifiedSteps.length"
        :label="`Modified Steps (${modifiedSteps.length})`"
        color="amber"
        :default-open="true"
      >
        <div class="space-y-3">
          <div
            v-for="step in modifiedSteps"
            :key="step.id"
            class="border-l-4 border-amber-500 bg-gray-800/30 backdrop-blur rounded-xl p-4"
          >
            <div class="flex items-start gap-3">
              <div class="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Pencil :size="14" class="text-amber-400" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-white truncate">{{ step.label || step.id }}</p>
                <p v-if="step.module_id" class="text-xs text-gray-500 font-mono mt-0.5">{{ step.module_id }}</p>
                <!-- Changed fields -->
                <div v-if="step._changedFields?.length" class="mt-2 flex flex-wrap gap-1.5">
                  <span
                    v-for="field in step._changedFields"
                    :key="field"
                    class="px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-md text-xs font-mono"
                  >
                    {{ field }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </DiffSection>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Plus, Minus, Pencil } from 'lucide-vue-next'
import DiffSection from './DiffSection.vue'

const props = defineProps({
  diffSummary: {
    type: Object,
    default: () => ({ added_steps: [], removed_steps: [], modified_steps: [] }),
  },
  proposedWorkflow: {
    type: Object,
    default: () => ({ steps: [] }),
  },
  /** Optional: base workflow steps, used to compute changed fields for modified steps */
  baseSteps: {
    type: Array,
    default: () => [],
  },
})

const proposedStepsMap = computed(() => {
  const map = {}
  for (const step of props.proposedWorkflow?.steps || []) {
    if (step.id) map[step.id] = step
  }
  return map
})

const baseStepsMap = computed(() => {
  const map = {}
  for (const step of props.baseSteps || []) {
    if (step.id) map[step.id] = step
  }
  return map
})

const addedSteps = computed(() => {
  return (props.diffSummary?.added_steps || []).map(id => {
    return proposedStepsMap.value[id] || { id }
  })
})

const removedSteps = computed(() => {
  return props.diffSummary?.removed_steps || []
})

const modifiedSteps = computed(() => {
  return (props.diffSummary?.modified_steps || []).map(id => {
    const proposed = proposedStepsMap.value[id] || { id }
    const base = baseStepsMap.value[id]
    const changedFields = base ? computeChangedFields(base, proposed) : []
    return { ...proposed, _changedFields: changedFields }
  })
})

const totalChanges = computed(() => {
  return addedSteps.value.length + removedSteps.value.length + modifiedSteps.value.length
})

/**
 * Compare two step objects and return a list of field names that differ.
 * Skips internal fields (id, _changedFields).
 */
function computeChangedFields(base, proposed) {
  const skip = new Set(['id', '_changedFields'])
  const allKeys = new Set([...Object.keys(base), ...Object.keys(proposed)])
  const changed = []
  for (const key of allKeys) {
    if (skip.has(key)) continue
    if (JSON.stringify(base[key]) !== JSON.stringify(proposed[key])) {
      changed.push(key)
    }
  }
  return changed
}
</script>

<style scoped>
.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}
@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
