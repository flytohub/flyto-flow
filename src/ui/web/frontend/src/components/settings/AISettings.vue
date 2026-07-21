<template>
  <div class="group relative bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:border-emerald-500/30 transition-all duration-500">
    <div class="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
    <div class="relative">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
            <Bot :size="20" class="text-white" />
          </div>
          <div>
            <h2 class="text-lg font-semibold text-white">{{ $t('userSettings.aiAssistant', 'AI Assistant') }}</h2>
            <p class="text-sm text-gray-400">{{ $t('userSettings.aiAssistantDesc', 'Configure your AI provider and API key') }}</p>
          </div>
        </div>
        <span v-if="store.isConfigured" class="flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-full bg-emerald-500/20 text-emerald-400">
          <CheckCircle :size="14" />
          {{ $t('userSettings.aiConfigured', 'Configured') }}
        </span>
      </div>

      <!-- Loading -->
      <div v-if="store.loading" class="flex items-center justify-center py-12">
        <Loader2 :size="24" class="animate-spin text-emerald-400" />
      </div>

      <div v-else class="space-y-6">
        <!-- Provider Selection -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">
            {{ $t('userSettings.aiProvider', 'Provider') }}
          </label>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <button
              v-for="p in providers"
              :key="p.id"
              :aria-label="p.label"
              @click="store.provider = p.id; store.clearTestResult()"
              :class="[
                'flex flex-col items-center gap-2 p-4 rounded-xl border transition-all',
                store.provider === p.id
                  ? 'border-emerald-500/50 bg-emerald-500/10 text-white'
                  : 'border-white/10 bg-gray-900/30 text-gray-400 hover:border-white/20 hover:text-gray-300'
              ]"
            >
              <component :is="p.icon" :size="24" />
              <span class="text-xs font-medium">{{ p.label }}</span>
            </button>
          </div>
        </div>

        <!-- API Key -->
        <div v-if="store.needsApiKey">
          <label class="block text-sm font-medium text-gray-300 mb-2">
            {{ $t('userSettings.aiApiKey', 'API Key') }}
          </label>
          <div class="relative">
            <AppInput
              v-model="apiKeyInput"
              :type="showApiKey ? 'text' : 'password'"
              :placeholder="store.apiKeyMasked || (store.provider === 'openai' ? 'sk-...' : 'sk-ant-...')"
            />
            <button
              @click="showApiKey = !showApiKey"
              aria-label="Toggle API key visibility"
              class="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-gray-400 hover:text-white transition-colors"
            >
              <EyeOff v-if="showApiKey" :size="16" />
              <Eye v-else :size="16" />
            </button>
          </div>
          <p class="text-xs text-gray-500 mt-1.5">
            {{ $t('userSettings.aiApiKeyHint', 'Your API key is encrypted and stored securely in the cloud.') }}
          </p>
        </div>

        <!-- Base URL (for OpenAI-compatible) -->
        <div v-if="store.needsBaseUrl">
          <label class="block text-sm font-medium text-gray-300 mb-2">
            {{ $t('userSettings.aiBaseUrl', 'Base URL') }}
          </label>
          <AppInput
            v-model="store.baseUrl"
            placeholder="https://api.example.com/v1"
          />
        </div>

        <!-- Model Selection -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">
            {{ $t('userSettings.aiModel', 'Model') }}
          </label>
          <AppSelect
            v-model="store.model"
            :options="[{ value: '', label: $t('userSettings.aiModelDefault', 'Default') }, ...allModels.map(m => ({ value: m, label: m }))]"
          />
        </div>

        <!-- Advanced Settings (collapsible) -->
        <div>
          <button
            @click="showAdvanced = !showAdvanced"
            class="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-300 transition-colors"
          >
            <ChevronDown
              :size="16"
              :class="['transition-transform', showAdvanced ? 'rotate-180' : '']"
            />
            {{ $t('userSettings.aiAdvanced', 'Advanced Settings') }}
          </button>

          <div v-if="showAdvanced" class="mt-4 space-y-4 pl-6 border-l border-white/10">
            <!-- Temperature -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-medium text-gray-300">
                  {{ $t('userSettings.aiTemperature', 'Temperature') }}
                </label>
                <span class="text-sm text-emerald-400 font-mono">{{ store.temperature.toFixed(1) }}</span>
              </div>
              <input
                v-model.number="store.temperature"
                type="range"
                min="0"
                max="2"
                step="0.1"
                class="w-full accent-emerald-500"
              />
              <div class="flex justify-between text-xs text-gray-500 mt-1">
                <span>{{ $t('userSettings.aiPrecise', 'Precise') }}</span>
                <span>{{ $t('userSettings.aiCreative', 'Creative') }}</span>
              </div>
            </div>

            <!-- Max Tokens -->
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">
                {{ $t('userSettings.aiMaxTokens', 'Max Tokens') }}
              </label>
              <input
                v-model.number="store.maxTokens"
                type="number"
                min="256"
                max="128000"
                step="256"
                class="w-full px-4 py-3 bg-gray-900/50 border border-white/10 rounded-xl text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all text-sm"
              />
            </div>
          </div>
        </div>

        <!-- AI Behavior -->
        <div class="space-y-3 pt-2 border-t border-white/10">
          <h3 class="text-sm font-medium text-gray-300">
            {{ $t('userSettings.aiBehavior', 'AI Behavior') }}
          </h3>
          <label class="flex items-center justify-between cursor-pointer group">
            <div>
              <span class="text-sm text-gray-300 group-hover:text-white transition-colors">
                {{ $t('userSettings.aiAutoImport', 'Auto Import') }}
              </span>
              <p class="text-xs text-gray-500">
                {{ $t('userSettings.aiAutoImportDesc', 'Automatically import AI-generated workflows to the builder') }}
              </p>
            </div>
            <div class="relative">
              <input type="checkbox" v-model="store.autoImport" class="sr-only peer" />
              <div class="w-10 h-5 bg-gray-700 peer-focus:ring-2 peer-focus:ring-emerald-500/50 rounded-full peer peer-checked:bg-emerald-600 transition-colors"></div>
              <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
            </div>
          </label>
          <label class="flex items-center justify-between cursor-pointer group">
            <div>
              <span class="text-sm text-gray-300 group-hover:text-white transition-colors">
                {{ $t('userSettings.aiAutoExecute', 'Auto Execute') }}
              </span>
              <p class="text-xs text-gray-500">
                {{ $t('userSettings.aiAutoExecuteDesc', 'Automatically execute workflows after import') }}
              </p>
            </div>
            <div class="relative">
              <input type="checkbox" v-model="store.autoExecute" class="sr-only peer" />
              <div class="w-10 h-5 bg-gray-700 peer-focus:ring-2 peer-focus:ring-emerald-500/50 rounded-full peer peer-checked:bg-emerald-600 transition-colors"></div>
              <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
            </div>
          </label>
        </div>

        <!-- Test Result -->
        <div v-if="store.testResult" :class="[
          'p-4 rounded-xl border flex items-start gap-3',
          store.testResult.ok
            ? 'bg-emerald-500/10 border-emerald-500/30'
            : 'bg-red-500/10 border-red-500/30'
        ]">
          <CheckCircle v-if="store.testResult.ok" :size="20" class="text-emerald-400 mt-0.5 flex-shrink-0" />
          <AlertCircle v-else :size="20" class="text-red-400 mt-0.5 flex-shrink-0" />
          <div>
            <p :class="store.testResult.ok ? 'text-emerald-400' : 'text-red-400'" class="text-sm font-medium">
              {{ store.testResult.message || store.testResult.error }}
            </p>
            <p v-if="store.testResult.ok && store.testResult.models?.length" class="text-xs text-gray-400 mt-1">
              {{ store.testResult.models.length }} {{ $t('userSettings.aiModelsAvailable', 'models available') }}
            </p>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex items-center gap-3 pt-2">
          <button
            @click="handleTest"
            :disabled="store.testing || (store.needsApiKey && !apiKeyInput && !store.apiKeyMasked)"
            class="flex items-center gap-2 px-4 py-2.5 bg-gray-700/50 text-gray-300 border border-white/10 rounded-xl hover:bg-gray-700/80 hover:text-white transition-all text-sm disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Loader2 v-if="store.testing" :size="16" class="animate-spin" />
            <Zap v-else :size="16" />
            {{ store.testing ? $t('userSettings.aiTesting', 'Testing...') : $t('userSettings.aiTestConnection', 'Test Connection') }}
          </button>

          <button
            @click="handleSave"
            :disabled="store.saving"
            class="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-emerald-600 to-cyan-600 text-white rounded-xl hover:shadow-lg hover:shadow-emerald-500/20 transition-all text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Loader2 v-if="store.saving" :size="16" class="animate-spin" />
            <Save v-else :size="16" />
            {{ store.saving ? $t('userSettings.saving', 'Saving...') : $t('userSettings.save', 'Save') }}
          </button>
        </div>

        <!-- Save Success -->
        <div v-if="saveSuccess" class="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm flex items-center gap-2">
          <CheckCircle :size="16" />
          {{ $t('userSettings.aiSaveSuccess', 'AI settings saved successfully') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import { useAISettingsStore } from '@/stores/aiSettingsStore'
import {
  Bot,
  CheckCircle,
  Loader2,
  Eye,
  EyeOff,
  ChevronDown,
  AlertCircle,
  Zap,
  Save,
  Sparkles,
  Cloud,
  Plug,
} from 'lucide-vue-next'

const store = useAISettingsStore()

const apiKeyInput = ref('')
const showApiKey = ref(false)
const showAdvanced = ref(false)
const saveSuccess = ref(false)

const providers = [
  { id: 'openai', label: 'OpenAI', icon: Sparkles },
  { id: 'anthropic', label: 'Anthropic', icon: Cloud },
  { id: 'openai-compatible', label: 'Compatible', icon: Plug },
]

const allModels = computed(() => {
  // Merge default models with any discovered from test
  const defaults = store.defaultModels
  const discovered = store.availableModels
  const merged = [...new Set([...defaults, ...discovered])]
  return merged
})

onMounted(() => {
  store.loadConfig()
})

async function handleTest() {
  await store.testConnection(apiKeyInput.value || undefined)
}

async function handleSave() {
  saveSuccess.value = false
  const result = await store.saveConfig({
    apiKey: apiKeyInput.value || undefined
  })
  if (result.ok) {
    saveSuccess.value = true
    apiKeyInput.value = ''
    setTimeout(() => { saveSuccess.value = false }, 3000)
  }
}
</script>
