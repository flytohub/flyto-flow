<template>
  <form class="integration-form" @submit.prevent="handleSubmit">
    <!-- Provider Selection (only for create) -->
    <div v-if="!integration" class="form-section">
      <label class="form-label">選擇平台</label>
      <div class="provider-grid">
        <button
          v-for="provider in providers"
          :key="provider.name"
          type="button"
          class="provider-option"
          :class="{ selected: selectedProvider === provider.name }"
          @click="selectProvider(provider.name)"
        >
          <div
            class="provider-icon"
            :style="{ backgroundColor: provider.color }"
          >
            <component :is="getProviderIcon(provider.name)" class="icon" />
          </div>
          <span class="provider-name">{{ provider.displayName }}</span>
        </button>
      </div>
    </div>

    <!-- Integration Name -->
    <div class="form-group">
      <label class="form-label">整合名稱</label>
      <AppInput
        v-model="form.name"
        placeholder="例如：我的 LINE Bot"
        required
      />
    </div>

    <!-- Description -->
    <div class="form-group">
      <label class="form-label">描述（選填）</label>
      <AppTextarea
        v-model="form.description"
        :rows="2"
        placeholder="這個整合的用途..."
      />
    </div>

    <!-- Provider Config -->
    <div v-if="providerSchema" class="form-section">
      <label class="form-label">{{ providerSchema.displayName }} 設定</label>
      <p class="setup-hint" v-if="providerSchema.setupInstructions">
        {{ providerSchema.setupInstructions }}
      </p>

      <div
        v-for="(fieldSchema, fieldName) in providerSchema.configSchema?.properties"
        :key="fieldName"
        class="form-group"
      >
        <label class="form-label">
          {{ fieldSchema.title || fieldName }}
          <span v-if="isRequired(fieldName)" class="required">*</span>
        </label>
        <AppInput
          v-if="fieldSchema.secret"
          type="password"
          v-model="form.config[fieldName]"
          :placeholder="fieldSchema.placeholder || ''"
          :required="isRequired(fieldName)"
        />
        <AppInput
          v-else
          v-model="form.config[fieldName]"
          :placeholder="fieldSchema.placeholder || ''"
          :required="isRequired(fieldName)"
        />
        <p v-if="fieldSchema.description" class="field-hint">
          {{ fieldSchema.description }}
        </p>
      </div>
    </div>

    <!-- Workflow Binding -->
    <div class="form-group">
      <label class="form-label">預設 Workflow（選填）</label>
      <AppSelect
        v-model="form.defaultWorkflowId"
        :options="[{ value: '', label: $t('common.noOptions', 'None') }, ...workflows.map(wf => ({ value: wf.id, label: wf.name }))]"
      />
      <p class="field-hint">收到訊息時自動執行的 Workflow</p>
    </div>

    <!-- Actions -->
    <div class="form-actions">
      <button type="button" class="btn btn-secondary" @click="$emit('cancel')">
        取消
      </button>
      <button type="submit" class="btn btn-primary" :disabled="!isValid || loading">
        <Loader2 v-if="loading" class="icon spinning" />
        {{ integration ? '儲存變更' : '建立整合' }}
      </button>
    </div>
  </form>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { getProviderSchema } from '@/api/messaging'
import { useTemplateStore } from '@/stores'
import { Loader2, MessageCircle, Send, Hash, MessageSquare } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'

const props = defineProps({
  providers: {
    type: Array,
    required: true,
  },
  integration: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['submit', 'cancel'])

// State
const loading = ref(false)
const selectedProvider = ref('')
const providerSchema = ref(null)
const templateStore = useTemplateStore()
const workflows = computed(() => templateStore.templates)

const form = ref({
  name: '',
  description: '',
  config: {},
  defaultWorkflowId: '',
})

// Provider icons
const providerIcons = {
  line: MessageCircle,
  telegram: Send,
  slack: Hash,
  discord: MessageSquare,
}

function getProviderIcon(provider) {
  return providerIcons[provider] || MessageSquare
}

// Initialize form and load workflows
onMounted(async () => {
  if (!templateStore.templates.length) {
    await templateStore.fetchTemplates()
  }
  if (props.integration) {
    form.value.name = props.integration.name || ''
    form.value.description = props.integration.description || ''
    form.value.defaultWorkflowId = props.integration.defaultWorkflowId || ''
    selectedProvider.value = props.integration.provider
    loadProviderSchema(props.integration.provider)
  }
})

// Select provider
function selectProvider(provider) {
  selectedProvider.value = provider
  form.value.config = {}
  loadProviderSchema(provider)
}

// Load provider schema
async function loadProviderSchema(provider) {
  try {
    const result = await getProviderSchema(provider)
    if (result.ok) {
      providerSchema.value = result
    }
  } catch (e) {
    console.error('Failed to load provider schema:', e)
  }
}

// Check if field is required
function isRequired(fieldName) {
  const required = providerSchema.value?.configSchema?.required || []
  return required.includes(fieldName)
}

// Validate form
const isValid = computed(() => {
  if (!selectedProvider.value) return false
  if (!form.value.name.trim()) return false

  // Check required config fields
  if (providerSchema.value?.configSchema?.required) {
    for (const field of providerSchema.value.configSchema.required) {
      if (!form.value.config[field]) return false
    }
  }

  return true
})

// Submit form
async function handleSubmit() {
  if (!isValid.value) return

  loading.value = true

  try {
    const data = {
      provider: selectedProvider.value,
      name: form.value.name.trim(),
      description: form.value.description.trim() || undefined,
      config: form.value.config,
      defaultWorkflowId: form.value.defaultWorkflowId || undefined,
    }

    emit('submit', data)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.integration-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-section {
  margin-bottom: 8px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-weight: 500;
  font-size: 14px;
  color: var(--text-primary);
}

.required {
  color: var(--danger);
}

.form-input {
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
}

.form-input::placeholder {
  color: var(--text-tertiary);
}

.field-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
}

.setup-hint {
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  white-space: pre-wrap;
}

.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
  margin-top: 8px;
}

.provider-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border: 2px solid var(--border-color);
  border-radius: 12px;
  background: var(--bg-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.provider-option:hover {
  border-color: var(--primary-light);
}

.provider-option.selected {
  border-color: var(--primary);
  background: var(--primary-bg);
}

.provider-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.provider-icon .icon {
  width: 24px;
  height: 24px;
}

.provider-option .provider-name {
  font-weight: 500;
  font-size: 14px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn .icon {
  width: 16px;
  height: 16px;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
