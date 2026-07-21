<template>
  <div class="var-tabs">
    <button
      v-for="tab in visibleTabs"
      :key="tab.id"
      :class="['var-tab', { active: activeTab === tab.id }]"
      @click="$emit('update:activeTab', tab.id)"
    >
      <component :is="tab.icon" :size="14" />
      <span>{{ $t(tab.labelKey) }}</span>
      <span v-if="getCount(tab.id) > 0" class="tab-count">
        {{ getCount(tab.id) }}
      </span>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FormInput, Layers, Settings } from 'lucide-vue-next'
import { VARIABLE_SOURCES } from '@/constants/templateBuilder/bindingTypes'

const TAB_CONFIG = [
  { id: 'inputs', labelKey: 'variableSelector.tabs.inputs', icon: FormInput, source: VARIABLE_SOURCES.UI_INPUTS },
  { id: 'steps', labelKey: 'variableSelector.tabs.steps', icon: Layers, source: VARIABLE_SOURCES.STEPS },
  { id: 'env', labelKey: 'variableSelector.tabs.env', icon: Settings, source: VARIABLE_SOURCES.ENV }
]

const props = defineProps({
  activeTab: { type: String, required: true },
  availableVariables: { type: Object, default: () => ({}) }
})

defineEmits(['update:activeTab'])

const visibleTabs = computed(() => {
  return TAB_CONFIG.filter(tab => {
    const vars = props.availableVariables[tab.id]
    return vars && vars.length > 0
  })
})

function getCount(tabId) {
  const vars = props.availableVariables[tabId]
  return vars ? vars.length : 0
}
</script>

<style scoped>
.var-tabs {
  display: flex;
  gap: 2px;
  padding: 8px;
  background: rgba(15, 23, 42, 0.6);
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.var-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.var-tab:hover {
  background: rgba(71, 85, 105, 0.3);
  color: #94a3b8;
}

.var-tab.active {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}

.tab-count {
  padding: 2px 6px;
  background: rgba(71, 85, 105, 0.4);
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
}

.var-tab.active .tab-count {
  background: rgba(139, 92, 246, 0.3);
}
</style>
