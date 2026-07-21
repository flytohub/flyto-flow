<script setup>
/**
 * HttpNodeParamsSimplified - Refactored HTTP Request Node Parameters
 *
 * Uses Progressive Disclosure pattern:
 * - Basic: URL + Method (what users need 90% of the time)
 * - Standard: Headers, Query, Body, Auth (tabs)
 * - Advanced: Timeout, SSL, Redirects
 *
 * Compatible with existing interface:
 * - Props: params, readOnly
 * - Emit: update:params
 */
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Terminal, ChevronRight } from 'lucide-vue-next'

// Components
import AppInput from '@/components/common/AppInput.vue'
import ProgressiveForm from '@/components/common/ProgressiveForm.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import KeyValueEditor from './shared/KeyValueEditor.vue'
import AuthConfigEditor from './shared/AuthConfigEditor.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'

const { t } = useI18n()

const props = defineProps({
  params: {
    type: Object,
    default: () => ({})
  },
  readOnly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:params'])

// === Local State ===
const localParams = ref({
  method: 'GET',
  url: '',
  headers: {},
  query: {},
  body: null,
  contentType: 'application/json',
  auth: null,
  timeout: 30000,
  followRedirects: true,
  verifySsl: true
})

// Disclosure state
const showStandard = ref(false)
const showAdvanced = ref(false)

// Active tab in standard section
const activeTab = ref('headers')

// HTTP Methods
const methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']

// === Sync with props ===
watch(() => props.params, (newParams) => {
  if (newParams) {
    localParams.value = {
      method: newParams.method || 'GET',
      url: newParams.url || '',
      headers: newParams.headers || {},
      query: newParams.query || {},
      body: newParams.body || null,
      contentType: newParams.contentType || 'application/json',
      auth: newParams.auth || null,
      timeout: newParams.timeout ?? 30000,
      followRedirects: newParams.followRedirects ?? true,
      verifySsl: newParams.verifySsl ?? true
    }

    // Auto-expand if has data
    if (Object.keys(localParams.value.headers).length > 0 ||
        Object.keys(localParams.value.query).length > 0 ||
        localParams.value.body) {
      showStandard.value = true
    }

    if (localParams.value.timeout !== 30000 ||
        !localParams.value.followRedirects ||
        !localParams.value.verifySsl) {
      showAdvanced.value = true
    }
  }
}, { immediate: true, deep: true })

// === Emit updates ===
function emitUpdate() {
  const params = { ...localParams.value }
  // Clean empty objects so deep merge doesn't preserve stale keys
  if (params.query && Object.keys(params.query).length === 0) {
    params.query = null
  }
  if (params.headers && Object.keys(params.headers).length === 0) {
    params.headers = null
  }
  emit('update:params', params)
}

// === Computed ===

// Badge counts
const headerCount = computed(() => {
  const h = localParams.value.headers
  return Array.isArray(h) ? h.length : Object.keys(h || {}).length
})

const queryCount = computed(() => {
  const q = localParams.value.query
  return Array.isArray(q) ? q.length : Object.keys(q || {}).length
})

const standardBadge = computed(() => {
  const total = headerCount.value + queryCount.value
  return total > 0 ? total : null
})

// HTTP method color
const methodColor = computed(() => {
  const colors = {
    GET: '#22c55e',
    POST: '#3b82f6',
    PUT: '#f59e0b',
    PATCH: '#a855f7',
    DELETE: '#ef4444',
    HEAD: '#64748b',
    OPTIONS: '#64748b'
  }
  return colors[localParams.value.method] || '#64748b'
})

// Tabs with counts
const tabs = computed(() => [
  { id: 'headers', label: t('http.headers', 'Headers'), count: headerCount.value },
  { id: 'query', label: t('http.query', 'Query'), count: queryCount.value },
  { id: 'body', label: t('http.body', 'Body'), count: localParams.value.body ? 1 : 0 },
  { id: 'auth', label: t('http.auth', 'Auth'), count: localParams.value.auth ? 1 : 0 }
])
</script>

<template>
  <div class="http-params-simplified">
    <ProgressiveForm
      v-model:standard-open="showStandard"
      v-model:advanced-open="showAdvanced"
      :standard-title="t('http.options', 'Options')"
      :advanced-title="t('http.advanced', 'Advanced')"
      :standard-badge="standardBadge"
      compact
    >
      <!-- ================================ -->
      <!-- BASIC: URL + Method              -->
      <!-- ================================ -->
      <template #basic>
        <div class="url-bar">
          <!-- Method Selector -->
          <AppSelect
            v-model="localParams.method"
            :options="methods.map(m => ({ value: m, label: m }))"
            :disabled="readOnly"
            @change="emitUpdate"
          />

          <!-- URL Input -->
          <AppInput
            v-model="localParams.url"
            :placeholder="t('http.url', 'https://api.example.com/endpoint')"
            :readonly="readOnly"
            @update:modelValue="emitUpdate"
            size="sm"
          />

          <!-- Import Button -->
          <button
            v-if="!readOnly"
            type="button"
            class="import-btn"
            :title="t('http.importCurl', 'Import cURL')"
          >
            <Terminal :size="14" />
          </button>
        </div>
      </template>

      <!-- ================================ -->
      <!-- STANDARD: Headers, Query, Body   -->
      <!-- ================================ -->
      <template #standard>
        <!-- Tabs -->
        <div class="params-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            type="button"
            class="tab-btn"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
            <span v-if="tab.count > 0" class="tab-badge">{{ tab.count }}</span>
          </button>
        </div>

        <!-- Tab Content -->
        <div class="tab-content">
          <!-- Headers Tab -->
          <div v-show="activeTab === 'headers'" class="tab-panel">
            <KeyValueEditor
              v-model="localParams.headers"
              :key-placeholder="t('http.headerKey', 'Header')"
              :value-placeholder="t('http.headerValue', 'Value')"
              :read-only="readOnly"
              @update:model-value="emitUpdate"
            />
          </div>

          <!-- Query Tab -->
          <div v-show="activeTab === 'query'" class="tab-panel">
            <KeyValueEditor
              v-model="localParams.query"
              :key-placeholder="t('http.paramKey', 'Parameter')"
              :value-placeholder="t('http.paramValue', 'Value')"
              :read-only="readOnly"
              @update:model-value="emitUpdate"
            />
          </div>

          <!-- Body Tab -->
          <div v-show="activeTab === 'body'" class="tab-panel">
            <AppTextarea
              v-model="localParams.body"
              :placeholder="t('http.bodyPlaceholder', '{ key: value }')"
              :readonly="readOnly"
              :rows="5"
              size="sm"
              @update:modelValue="emitUpdate"
            />
          </div>

          <!-- Auth Tab -->
          <div v-show="activeTab === 'auth'" class="tab-panel">
            <AuthConfigEditor
              v-model="localParams.auth"
              :read-only="readOnly"
              @update:model-value="emitUpdate"
            />
          </div>
        </div>
      </template>

      <!-- ================================ -->
      <!-- ADVANCED: Timeout, SSL, etc.     -->
      <!-- ================================ -->
      <template #advanced>
        <div class="advanced-grid">
          <!-- Timeout -->
          <div class="field-row">
            <label class="field-label">{{ t('http.timeout', 'Timeout (ms)') }}</label>
            <NumberInput
              v-model="localParams.timeout"
              :min="0"
              :max="300000"
              :step="1000"
              :disabled="readOnly"
              @update:model-value="emitUpdate"
            />
          </div>

          <!-- Follow Redirects -->
          <div class="field-row">
            <label class="checkbox-label">
              <input
                type="checkbox"
                v-model="localParams.followRedirects"
                :disabled="readOnly"
                @change="emitUpdate"
              />
              {{ t('http.followRedirects', 'Follow Redirects') }}
            </label>
          </div>

          <!-- Verify SSL -->
          <div class="field-row">
            <label class="checkbox-label">
              <input
                type="checkbox"
                v-model="localParams.verifySsl"
                :disabled="readOnly"
                @change="emitUpdate"
              />
              {{ t('http.verifySsl', 'Verify SSL Certificate') }}
            </label>
          </div>
        </div>
      </template>
    </ProgressiveForm>
  </div>
</template>

<style scoped>
.http-params-simplified {
  /* Container */
}

/* === URL Bar === */
.url-bar {
  display: flex;
  gap: 8px;
  align-items: center;
}

.url-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-secondary, #334155);
  border-radius: 6px;
  background: var(--bg-secondary, rgba(30, 41, 59, 0.5));
  color: var(--text-primary, #f1f5f9);
  font-size: 13px;
}

.url-input:focus {
  outline: none;
  border-color: var(--primary, #8B5CF6);
}

.url-input[readonly] {
  opacity: 0.7;
  cursor: default;
}

.import-btn {
  padding: 8px;
  border: 1px solid var(--border-secondary, #334155);
  border-radius: 6px;
  background: var(--bg-secondary, rgba(30, 41, 59, 0.5));
  color: var(--text-muted, #64748b);
  cursor: pointer;
  transition: all 0.15s ease;
}

.import-btn:hover {
  background: var(--bg-hover, rgba(139, 92, 246, 0.1));
  color: var(--text-primary, #f1f5f9);
}

/* === Tabs === */
.params-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--border-secondary, #334155);
  padding-bottom: 8px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--text-muted, #64748b);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.tab-btn:hover {
  background: var(--bg-hover, rgba(139, 92, 246, 0.1));
  color: var(--text-secondary, #94a3b8);
}

.tab-btn.active {
  background: var(--primary-muted, rgba(139, 92, 246, 0.15));
  color: var(--primary-light, #c4b5fd);
}

.tab-badge {
  padding: 2px 6px;
  border-radius: 10px;
  background: var(--bg-tertiary, rgba(139, 92, 246, 0.2));
  font-size: 11px;
}

/* === Tab Content === */
.tab-content {
  min-height: 80px;
}

.tab-panel {
  /* Content styling */
}

.body-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-secondary, #334155);
  border-radius: 6px;
  background: var(--bg-secondary, rgba(30, 41, 59, 0.5));
  color: var(--text-primary, #f1f5f9);
  font-family: monospace;
  font-size: 12px;
  resize: vertical;
}

.body-textarea:focus {
  outline: none;
  border-color: var(--primary, #8B5CF6);
}

.placeholder-text {
  color: var(--text-muted, #64748b);
  font-size: 13px;
  text-align: center;
  padding: 24px;
}

/* === Advanced Grid === */
.advanced-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.field-label {
  font-size: 13px;
  color: var(--text-secondary, #94a3b8);
  min-width: 100px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary, #94a3b8);
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--primary, #8B5CF6);
}

.checkbox-label input[type="checkbox"]:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
