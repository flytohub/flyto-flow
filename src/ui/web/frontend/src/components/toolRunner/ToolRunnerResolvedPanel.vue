<template>
  <div class="resolved-panel">
    <div class="panel-header">
      <Code :size="18" />
      <span>{{ $t('toolRunner.resolvedParams') }}</span>
      <button class="toggle-btn" @click="toggleExpanded">
        <ChevronDown :size="14" :class="{ 'rotate-180': expanded }" />
      </button>
    </div>

    <div v-if="expanded" class="resolved-content">
      <div
        v-for="(step, idx) in steps"
        :key="step.id"
        class="resolved-step"
      >
        <div class="resolved-step-header">
          <span class="step-idx">{{ idx + 1 }}</span>
          <span class="step-name">{{ resolveModuleLabel(step.module, modulesStore) }}</span>
        </div>
        <pre class="resolved-json">{{ JSON.stringify(resolveParams(step), null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Code, ChevronDown } from 'lucide-vue-next'
import { useModulesStore } from '@/stores/modulesStore'
import { resolveModuleLabel } from '@/utils/moduleIdUtils'

const modulesStore = useModulesStore()

const props = defineProps({
  steps: {
    type: Array,
    default: () => []
  },
  inputValues: {
    type: Object,
    default: () => ({})
  }
})

const expanded = ref(true)

function toggleExpanded() {
  expanded.value = !expanded.value
}

function resolveParams(step) {
  const resolved = {}

  for (const [paramName, source] of Object.entries(step.params || {})) {
    if (source.from === 'input' && source.key) {
      const val = props.inputValues[source.key]
      resolved[paramName] = val instanceof File ? `[File: ${val.name}]` : val
    } else if (source.from === 'step' && source.stepId) {
      resolved[paramName] = `{{ steps.${source.stepId}.output.${source.output || 'result'} }}`
    } else if (source.from === 'fixed') {
      resolved[paramName] = source.value
    }
  }

  return resolved
}
</script>

<style scoped>
.resolved-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 16px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background: rgba(51, 65, 85, 0.5);
  border-bottom: 1px solid #334155;
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
}

.toggle-btn {
  margin-left: auto;
  display: flex;
  align-items: center;
  padding: 4px;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn:hover {
  color: #94a3b8;
}

.toggle-btn .rotate-180 {
  transform: rotate(180deg);
}

.resolved-content {
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.resolved-step {
  margin-bottom: 12px;
}

.resolved-step:last-child {
  margin-bottom: 0;
}

.resolved-step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.step-idx {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #334155;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
}

.step-name {
  font-size: 12px;
  font-weight: 500;
  color: #f1f5f9;
}

.resolved-json {
  margin: 0;
  padding: 8px 10px;
  background: #0f172a;
  border-radius: 6px;
  font-family: 'Fira Code', monospace;
  font-size: 11px;
  color: #94a3b8;
  overflow-x: auto;
}
</style>
