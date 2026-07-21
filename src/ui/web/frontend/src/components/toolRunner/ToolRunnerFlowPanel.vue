<template>
  <div class="flow-panel">
    <div class="panel-header">
      <Workflow :size="18" />
      <span>{{ $t('toolRunner.flowSteps') }}</span>
    </div>

    <div class="flow-steps">
      <div
        v-for="(step, idx) in steps"
        :key="step.id"
        class="flow-step"
        :class="{
          completed: currentStepIndex > idx,
          active: currentStepIndex === idx,
          pending: currentStepIndex < idx || currentStepIndex === -1
        }"
      >
        <div class="step-connector" v-if="idx > 0"></div>
        <div class="step-node">
          <div class="step-icon">
            <CheckCircle v-if="currentStepIndex > idx" :size="18" />
            <Loader v-else-if="currentStepIndex === idx" :size="18" class="spin" />
            <Box v-else :size="18" />
          </div>
          <div class="step-info">
            <span class="step-label">{{ resolveModuleLabel(step.module, modulesStore) }}</span>
            <span class="step-module">{{ step.module }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Workflow, CheckCircle, Loader, Box } from 'lucide-vue-next'
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
</script>

<style scoped>
.flow-panel {
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

.flow-steps {
  padding: 20px;
}

.flow-step {
  position: relative;
}

.step-connector {
  position: absolute;
  left: 21px;
  top: -20px;
  width: 2px;
  height: 20px;
  background: #334155;
}

.flow-step.completed .step-connector {
  background: #10b981;
}

.flow-step.active .step-connector {
  background: linear-gradient(to bottom, #10b981, #3b82f6);
}

.step-node {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 10px;
  margin-bottom: 12px;
  transition: all 0.2s;
}

.flow-step.completed .step-node {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.flow-step.active .step-node {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.step-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #334155;
  border-radius: 8px;
  color: #64748b;
}

.flow-step.completed .step-icon {
  background: #10b981;
  color: white;
}

.flow-step.active .step-icon {
  background: #3b82f6;
  color: white;
}

.step-info {
  flex: 1;
}

.step-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #f1f5f9;
}

.step-module {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
