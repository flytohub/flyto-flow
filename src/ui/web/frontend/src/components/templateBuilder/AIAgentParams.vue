<template>
  <div class="ai-agent-params">
    <!-- Info Banner -->
    <div class="info-banner">
      <Bot :size="16" />
      <div class="info-text">
        <span class="info-title">{{ $t('aiAgent.shellInfo') || 'AI Agent Orchestrator' }}</span>
        <span class="info-desc">{{ $t('aiAgent.shellInfoDesc') || 'Add Model, Memory, Tools via buttons below the node' }}</span>
      </div>
    </div>

    <!-- Provider Selection Tabs -->
    <div class="provider-tabs">
      <button
        v-for="prov in providers"
        :key="prov.id"
        type="button"
        class="provider-tab"
        :class="{ active: localParams.provider === prov.id }"
        @click="setProvider(prov.id)"
      >
        <component :is="prov.icon" :size="14" />
        <span>{{ prov.label }}</span>
      </button>
    </div>

    <!-- Model Selection -->
    <div class="param-group">
      <label class="param-label">
        <Cpu :size="14" />
        {{ $t('aiAgent.model') || 'Model' }}
      </label>
      <AppSelect
        v-model="localParams.model"
        :options="currentModels.map(m => ({ value: m.id, label: m.name }))"
      />
    </div>

    <!-- Prompt Source Selection -->
    <div class="param-group">
      <label class="param-label">
        <MessageSquare :size="14" />
        {{ $t('aiAgent.promptSource') || 'Prompt Source' }}
      </label>
      <div class="source-tabs">
        <button
          type="button"
          class="source-tab"
          :class="{ active: localParams.promptSource === 'manual' }"
          @click="localParams.promptSource = 'manual'"
        >
          <Edit3 :size="14" />
          <span>{{ $t('aiAgent.manual') || 'Manual' }}</span>
        </button>
        <button
          type="button"
          class="source-tab"
          :class="{ active: localParams.promptSource === 'auto' }"
          @click="localParams.promptSource = 'auto'"
        >
          <ArrowRight :size="14" />
          <span>{{ $t('aiAgent.fromInput') || 'From Input' }}</span>
        </button>
      </div>
    </div>

    <!-- Manual Task Input -->
    <div v-if="localParams.promptSource === 'manual'" class="param-group">
      <PromptTemplateEditor
        v-model="localParams.task"
        :label="$t('aiAgent.task') || 'Task'"
        :placeholder="$t('aiAgent.taskPlaceholder') || 'Describe what the agent should do...'"
        :rows="4"
        :required="true"
        :available-variables="availableVariables"
        @insert-variable="openVariableSelector('task')"
      />
    </div>

    <!-- Auto Input Path -->
    <div v-else class="param-group">
      <label class="param-label">
        <Braces :size="14" />
        {{ $t('aiAgent.promptPath') || 'Input Path' }}
      </label>
      <div class="input-wrapper">
        <AppInput
          v-model="localParams.promptPath"
          :placeholder="'{{input}}'"
          size="sm"
        />
        <button
          type="button"
          class="var-btn"
          @click="showPathSelector = true"
          :title="$t('aiAgent.selectVariable') || 'Select variable'"
        >
          <Variable :size="14" />
        </button>
      </div>
      <p class="param-hint">{{ $t('aiAgent.promptPathHint') || 'Expression to get prompt from upstream node' }}</p>
    </div>

    <!-- System Prompt -->
    <div class="param-group">
      <PromptTemplateEditor
        v-model="localParams.systemPrompt"
        :label="$t('aiAgent.systemPrompt') || 'System Prompt'"
        :placeholder="$t('aiAgent.systemPromptPlaceholder') || 'You are a helpful AI agent...'"
        :rows="3"
        :show-detected-variables="false"
      />
    </div>

    <!-- Advanced Options -->
    <div class="advanced-section">
      <button
        type="button"
        class="advanced-toggle"
        @click="showAdvanced = !showAdvanced"
      >
        <ChevronRight :size="14" :class="{ rotated: showAdvanced }" />
        <span>{{ $t('aiAgent.advancedOptions') || 'Advanced Options' }}</span>
      </button>

      <Transition name="collapse">
        <div v-if="showAdvanced" class="advanced-content">
          <!-- Temperature -->
          <div class="param-group">
            <label class="param-label">
              <Thermometer :size="14" />
              {{ $t('aiAgent.temperature') || 'Temperature' }}
              <span class="param-value">{{ localParams.temperature }}</span>
            </label>
            <input
              v-model.number="localParams.temperature"
              type="range"
              min="0"
              max="2"
              step="0.1"
              class="param-slider"
            />
          </div>

          <!-- Max Iterations -->
          <div class="param-group">
            <label class="param-label">
              <Repeat :size="14" />
              {{ $t('aiAgent.maxIterations') || 'Max Iterations' }}
            </label>
            <input
              v-model.number="localParams.maxIterations"
              type="number"
              min="1"
              max="50"
              class="param-input"
            />
            <p class="param-hint">{{ $t('aiAgent.maxIterationsHint') || 'Maximum number of tool calls (1-50)' }}</p>
          </div>

          <!-- API Key -->
          <div class="param-group">
            <label class="param-label">
              <KeyRound :size="14" />
              {{ $t('aiAgent.apiKey') || 'API Key' }}
            </label>
            <AppInput
              v-model="localParams.apiKey"
              type="password"
              :placeholder="$t('aiAgent.apiKeyPlaceholder') || 'Leave empty to use environment variable'"
              size="sm"
            />
            <p class="param-hint">{{ $t('aiAgent.apiKeyHint') || 'Falls back to OPENAI_API_KEY / ANTHROPIC_API_KEY env var' }}</p>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed, markRaw } from 'vue'
import {
  Bot,
  Cpu,
  MessageSquare,
  Edit3,
  ArrowRight,
  Braces,
  Variable,
  ChevronRight,
  Thermometer,
  Repeat,
  KeyRound,
  CircuitBoard,
  Sparkles,
  Gem
} from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import PromptTemplateEditor from './shared/PromptTemplateEditor.vue'
import { useEngineVariables } from '@/composables/useEngineVariables'
import { useConfigStore } from '@/stores/configStore'

const props = defineProps({
  params: {
    type: Object,
    required: true
  },
  workflow: {
    type: Object,
    default: null
  },
  nodeId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:params'])

const showPathSelector = ref(false)
const showAdvanced = ref(false)

// Config store for LLM providers/models
const configStore = useConfigStore()

const ICON_MAP = {
  CircuitBoard: markRaw(CircuitBoard),
  Bot: markRaw(Bot),
  Sparkles: markRaw(Sparkles),
  Gem: markRaw(Gem)
}

const providers = computed(() => {
  return configStore.llmProviders.map(p => ({
    id: p.id,
    label: p.name,
    icon: ICON_MAP[p.icon] || markRaw(Bot)
  }))
})

const providerModels = computed(() => {
  const modelsMap = {}
  configStore.llmProviders.forEach(p => {
    modelsMap[p.id] = p.models || []
  })
  return modelsMap
})

const currentModels = computed(() => {
  return providerModels.value[localParams.provider] || []
})

// Use Engine SDK for variable introspection
const workflowRef = computed(() => props.workflow)
const nodeIdRef = computed(() => props.nodeId)
const { availableVariables } = useEngineVariables({
  workflow: workflowRef,
  nodeId: nodeIdRef
})

// Local reactive copy
const localParams = reactive({
  task: props.params.task || '',
  promptSource: props.params.promptSource || 'manual',
  promptPath: props.params.promptPath || '{{input}}',
  systemPrompt: props.params.systemPrompt || 'You are a helpful AI agent. Use the available tools to complete the task. Think step by step.',
  provider: props.params.provider || 'openai',
  model: props.params.model || 'gpt-4o',
  temperature: props.params.temperature ?? 0.3,
  maxIterations: props.params.maxIterations ?? 10,
  apiKey: props.params.apiKey || '',
})

function setProvider(providerId) {
  localParams.provider = providerId
  const models = providerModels.value[providerId]
  if (models && models.length > 0) {
    localParams.model = models[0].id
  }
}

function openVariableSelector(target) {
}

// Sync changes to parent
watch(
  localParams,
  (newParams) => {
    emit('update:params', { ...newParams })
  },
  { deep: true }
)

// Sync from parent
watch(
  () => props.params,
  (newParams) => {
    if (newParams.task !== undefined) localParams.task = newParams.task
    if (newParams.promptSource !== undefined) localParams.promptSource = newParams.promptSource
    if (newParams.promptPath !== undefined) localParams.promptPath = newParams.promptPath
    if (newParams.systemPrompt !== undefined) localParams.systemPrompt = newParams.systemPrompt
    if (newParams.provider !== undefined) localParams.provider = newParams.provider
    if (newParams.model !== undefined) localParams.model = newParams.model
    if (newParams.temperature !== undefined) localParams.temperature = newParams.temperature
    if (newParams.maxIterations !== undefined) localParams.maxIterations = newParams.maxIterations
    if (newParams.apiKey !== undefined) localParams.apiKey = newParams.apiKey
  },
  { deep: true }
)
</script>

<style scoped>
.ai-agent-params {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Info Banner */
.info-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.1) 0%, rgba(245, 158, 11, 0.1) 100%);
  border: 1px solid rgba(249, 115, 22, 0.2);
  border-radius: 10px;
  color: #f59e0b;
}

.info-banner > svg {
  flex-shrink: 0;
  margin-top: 2px;
}

.info-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.info-title {
  font-size: 12px;
  font-weight: 600;
  color: #fbbf24;
}

.info-desc {
  font-size: 11px;
  color: #d97706;
}

/* Provider Tabs */
.provider-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 8px;
}

.provider-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 8px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #64748b;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.provider-tab:hover {
  color: #94a3b8;
  background: rgba(71, 85, 105, 0.2);
}

.provider-tab.active {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}

/* Param Group */
.param-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.param-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: #94a3b8;
}

.param-value {
  margin-left: auto;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 11px;
  color: #a78bfa;
}

/* Param Hint */
.param-hint {
  margin: 0;
  font-size: 11px;
  color: #475569;
}

/* Source Tabs */
.source-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 8px;
}

.source-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
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

.source-tab:hover {
  color: #94a3b8;
  background: rgba(71, 85, 105, 0.2);
}

.source-tab.active {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}

/* Input with variable button */
.input-wrapper {
  display: flex;
  gap: 4px;
}

.param-input {
  flex: 1;
  padding: 10px 12px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 13px;
  font-family: 'SF Mono', Monaco, monospace;
  transition: all 0.2s ease;
}

.param-input:hover {
  border-color: rgba(71, 85, 105, 0.6);
}

.param-input:focus {
  outline: none;
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.1);
}

.param-input::placeholder {
  color: #475569;
}

.param-input[type="number"] {
  width: 100%;
}

.var-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  color: #a78bfa;
  cursor: pointer;
  transition: all 0.2s ease;
}

.var-btn:hover {
  background: rgba(139, 92, 246, 0.25);
  border-color: rgba(139, 92, 246, 0.5);
}

/* Advanced Section */
.advanced-section {
  border-top: 1px solid rgba(71, 85, 105, 0.2);
  padding-top: 8px;
}

.advanced-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 8px 4px;
  background: none;
  border: none;
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s ease;
}

.advanced-toggle:hover {
  color: #94a3b8;
}

.advanced-toggle svg {
  transition: transform 0.2s ease;
}

.advanced-toggle svg.rotated {
  transform: rotate(90deg);
}

.advanced-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-top: 8px;
}

/* Slider */
.param-slider {
  width: 100%;
  height: 4px;
  appearance: none;
  background: rgba(71, 85, 105, 0.4);
  border-radius: 2px;
  outline: none;
}

.param-slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #a78bfa;
  cursor: pointer;
  border: 2px solid rgba(15, 23, 42, 0.8);
}

/* Collapse Transition */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
