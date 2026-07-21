<template>
  <div class="var-list">
    <TransitionGroup name="var-item">
      <div v-if="variables.length === 0" key="empty" class="empty-state">
        <Package :size="24" />
        <span>{{ $t('variableSelector.noVariables') }}</span>
      </div>

      <VariableItem
        v-for="variable in variables"
        :key="variable.path"
        :variable="variable"
        :selected="selectedPath === variable.path"
        @select="$emit('select', $event)"
      />
    </TransitionGroup>
  </div>
</template>

<script setup>
import { Package } from 'lucide-vue-next'
import VariableItem from './VariableItem.vue'

defineProps({
  variables: { type: Array, default: () => [] },
  selectedPath: { type: String, default: null }
})

defineEmits(['select'])
</script>

<style scoped>
.var-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  min-height: 120px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px 16px;
  color: #475569;
  font-size: 12px;
}

.var-item-enter-active,
.var-item-leave-active {
  transition: all 0.2s ease;
}

.var-item-enter-from,
.var-item-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

.var-list::-webkit-scrollbar { width: 6px; }
.var-list::-webkit-scrollbar-track { background: transparent; }
.var-list::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.4);
  border-radius: 3px;
}
.var-list::-webkit-scrollbar-thumb:hover {
  background: rgba(71, 85, 105, 0.6);
}
</style>
