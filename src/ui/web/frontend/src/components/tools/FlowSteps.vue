<template>
  <div v-if="steps.length > 0" class="flow-details">
    <button class="toggle-details" @click="expanded = !expanded">
      <ChevronDown :size="16" :class="{ rotated: expanded }" />
      {{ $t('simpleToolView.viewSteps') }} ({{ steps.length }})
    </button>

    <div v-if="expanded" class="steps-list">
      <div
        v-for="(step, idx) in steps"
        :key="step.id"
        class="step-item"
        :class="{
          completed: currentStepIndex > idx,
          active: currentStepIndex === idx,
          pending: currentStepIndex < idx
        }"
      >
        <div class="step-number">
          <CheckCircle v-if="currentStepIndex > idx" :size="16" />
          <Loader v-else-if="currentStepIndex === idx" :size="16" class="spin" />
          <span v-else>{{ idx + 1 }}</span>
        </div>
        <span class="step-label">{{ resolveModuleLabel(step.module, modulesStore) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ChevronDown, CheckCircle, Loader } from 'lucide-vue-next'
import { useModulesStore } from '@/stores/modulesStore'
import { resolveModuleLabel } from '@/utils/moduleIdUtils'

const modulesStore = useModulesStore()

defineProps({
  steps: {
    type: Array,
    default: () => []
  },
  currentStepIndex: {
    type: Number,
    default: -1
  }
})

const expanded = ref(false)
</script>

<style scoped>
.flow-details {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #334155;
}

.toggle-details {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  cursor: pointer;
}

.toggle-details:hover {
  color: #94a3b8;
}

.toggle-details svg {
  transition: transform 0.2s;
}

.toggle-details svg.rotated {
  transform: rotate(180deg);
}

.steps-list {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: #1e293b;
  border-radius: 8px;
  font-size: 13px;
  color: #64748b;
}

.step-item.completed {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.step-item.active {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.step-number {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #334155;
  border-radius: 50%;
  font-size: 11px;
}

.step-item.completed .step-number {
  background: #10b981;
  color: white;
}

.step-item.active .step-number {
  background: #3b82f6;
  color: white;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
