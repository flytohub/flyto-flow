<template>
  <div class="llm-chain-params">
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <Loader2 :size="20" class="spin" />
      <span>Loading providers...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="configError" class="error-state">
      <span>Failed to load LLM config</span>
    </div>

    <template v-else>
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
        {{ $t('llmChain.model') }}
      </label>
      <AppSelect
        v-model="localParams.model"
        :options="currentModels.map(m => ({ value: m.id, label: m.name }))"
      />
    </div>

    <!-- System Prompt (Optional) -->
    <div class="param-group">
      <PromptTemplateEditor
        v-model="localParams.systemPrompt"
        :label="$t('llmChain.systemPrompt')"
        :placeholder="$t('llmChain.systemPromptPlaceholder')"
        :rows="3"
        :show-detected-variables="false"
        @insert-variable="openVariableSelector('system')"
      />
    </div>

    <!-- User Prompt -->
    <div class="param-group">
      <PromptTemplateEditor
        v-model="localParams.userPrompt"
        :label="$t('llmChain.userPrompt')"
        :placeholder="$t('llmChain.userPromptPlaceholder')"
        :rows="5"
        :required="true"
        @insert-variable="openVariableSelector('user')"
      />
      <p class="variable-hint">
        <Braces :size="12" />
        {{ $t('llmChain.variableHelp') }}
      </p>
    </div>

    <!-- Advanced Options (Collapsible) -->
    <div class="advanced-section">
      <button
        type="button"
        class="advanced-toggle"
        @click="showAdvanced = !showAdvanced"
      >
        <ChevronRight :size="14" :class="{ rotated: showAdvanced }" />
        <span>{{ $t('llmChain.advancedOptions') }}</span>
      </button>

      <Transition name="collapse">
        <div v-if="showAdvanced" class="advanced-content">
          <!-- Temperature -->
          <div class="param-group">
            <label class="param-label">
              <Thermometer :size="14" />
              {{ $t('llmChain.temperature') }}
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
            <p class="param-hint">{{ $t('llmChain.temperatureHint') }}</p>
          </div>

          <!-- Max Tokens -->
          <div class="param-group">
            <label class="param-label">
              <Hash :size="14" />
              {{ $t('llmChain.maxTokens') }}
            </label>
            <NumberInput
              v-model="localParams.maxTokens"
              :min="1"
              :max="128000"
              inputClass="param-input"
            />
            <p class="param-hint">{{ $t('llmChain.maxTokensHint') }}</p>
          </div>
        </div>
      </Transition>
    </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed, markRaw } from 'vue'
import {
  Cpu,
  ChevronRight,
  Thermometer,
  Hash,
  Braces,
  Bot,
  Sparkles,
  CircuitBoard,
  Gem,
  Loader2
} from 'lucide-vue-next'
import AppSelect from '@/components/common/AppSelect.vue'
import PromptTemplateEditor from './shared/PromptTemplateEditor.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import { useConfigStore } from '@/stores/configStore'

const props = defineProps({
  params: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:params'])

// Config store
const configStore = useConfigStore()

// Icon mapping from backend icon names to components
const ICON_MAP = {
  CircuitBoard: markRaw(CircuitBoard),
  Bot: markRaw(Bot),
  Sparkles: markRaw(Sparkles),
  Gem: markRaw(Gem)
}

// Loading state from store
const loading = computed(() => configStore.isLoading)
const configError = computed(() => configStore.error)

// Provider list with icons mapped
const providers = computed(() => {
  return configStore.llmProviders.map(p => ({
    id: p.id,
    label: p.name,
    icon: ICON_MAP[p.icon] || markRaw(Bot)
  }))
})

// Models lookup by provider
const providerModels = computed(() => {
  const modelsMap = {}
  configStore.llmProviders.forEach(p => {
    modelsMap[p.id] = p.models || []
  })
  return modelsMap
})

// Defaults from store
const defaults = computed(() => ({
  provider: configStore.defaultLLMProvider,
  model: configStore.defaultLLMModel,
  temperature: configStore.llm?.defaults?.temperature ?? 0.7,
  maxTokens: configStore.llm?.defaults?.maxTokens ?? 1000
}))

const showAdvanced = ref(false)

// Local reactive copy of params (use defaults from API)
const localParams = reactive({
  provider: props.params.provider || 'openai',
  model: props.params.model || 'gpt-4o',
  systemPrompt: props.params.systemPrompt || '',
  userPrompt: props.params.userPrompt || '',
  temperature: props.params.temperature ?? 0.7,
  maxTokens: props.params.maxTokens ?? 1000,
  stream: props.params.stream ?? false
})

// Current models based on provider (from API data)
const currentModels = computed(() => {
  return providerModels.value[localParams.provider] || []
})

// Set provider and reset model to first available
function setProvider(providerId) {
  localParams.provider = providerId
  const models = providerModels.value[providerId]
  if (models && models.length > 0) {
    localParams.model = models[0].id
  }
}

// Open variable selector (emits event for parent to handle)
function openVariableSelector(target) {
  // Could open a variable selector modal
  // For now, this is a placeholder for future enhancement
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
    if (newParams.provider !== undefined) localParams.provider = newParams.provider
    if (newParams.model !== undefined) localParams.model = newParams.model
    if (newParams.systemPrompt !== undefined) localParams.systemPrompt = newParams.systemPrompt
    if (newParams.userPrompt !== undefined) localParams.userPrompt = newParams.userPrompt
    if (newParams.temperature !== undefined) localParams.temperature = newParams.temperature
    if (newParams.maxTokens !== undefined) localParams.maxTokens = newParams.maxTokens
    if (newParams.stream !== undefined) localParams.stream = newParams.stream
  },
  { deep: true }
)
</script>

<style scoped>
.llm-chain-params {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Provider Tabs */
.provider-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 10px;
}

.provider-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: #64748b;
  font-size: 12px;
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
  color: #a78bfa;
  font-family: 'SF Mono', Monaco, monospace;
}

/* Variable Hint */
.variable-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 11px;
  color: #64748b;
}

/* Advanced Section */
.advanced-section {
  border-top: 1px solid rgba(71, 85, 105, 0.3);
  padding-top: 12px;
}

.advanced-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 0;
  background: transparent;
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
  padding-top: 12px;
}

/* Slider */
.param-slider {
  width: 100%;
  height: 6px;
  background: rgba(71, 85, 105, 0.4);
  border-radius: 3px;
  appearance: none;
  cursor: pointer;
}

.param-slider::-webkit-slider-thumb {
  width: 16px;
  height: 16px;
  background: #a78bfa;
  border: none;
  border-radius: 50%;
  appearance: none;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.param-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

/* Number Input */
.param-input {
  width: 100%;
  padding: 10px 12px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 13px;
  transition: all 0.2s ease;
}

.param-input:focus {
  outline: none;
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.1);
}

.param-hint {
  margin: 0;
  font-size: 11px;
  color: #475569;
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
  max-height: 300px;
}

/* Loading & Error States */
.loading-state,
.error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: #64748b;
  font-size: 13px;
}

.error-state {
  color: #ef4444;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
