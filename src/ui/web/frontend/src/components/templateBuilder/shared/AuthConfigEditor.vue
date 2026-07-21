<template>
  <div class="auth-config-editor">
    <!-- Auth Type Selector -->
    <div class="auth-field">
      <span class="auth-label">{{ t('http.authType.label', 'Auth Type') }}</span>
      <select
        class="auth-select"
        :value="authType"
        :disabled="readOnly"
        @change="onTypeChange($event.target.value)"
      >
        <option value="none">{{ t('http.authType.none', 'None') }}</option>
        <option value="bearer">{{ t('http.authType.bearer', 'Bearer Token') }}</option>
        <option value="basic">{{ t('http.authType.basic', 'Basic Auth') }}</option>
        <option value="api_key">{{ t('http.authType.apiKey', 'API Key') }}</option>
      </select>
    </div>

    <!-- Bearer Token Fields -->
    <div v-if="authType === 'bearer'" class="auth-fields">
      <div class="auth-field">
        <span class="auth-label">{{ t('http.token', 'Token') }}</span>
        <ValueSourceSelector
          :modelValue="localValue.token || ''"
          inputType="password"
          :placeholder="t('http.token', 'Token')"
          :readonly="readOnly"
          :uiInputFields="uiInputFields"
          :previousSteps="previousSteps"
          @update:modelValue="updateField('token', $event)"
        />
      </div>
    </div>

    <!-- Basic Auth Fields -->
    <div v-if="authType === 'basic'" class="auth-fields">
      <div class="auth-field">
        <span class="auth-label">{{ t('http.username', 'Username') }}</span>
        <ValueSourceSelector
          :modelValue="localValue.username || ''"
          inputType="text"
          :placeholder="t('http.username', 'Username')"
          :readonly="readOnly"
          :uiInputFields="uiInputFields"
          :previousSteps="previousSteps"
          @update:modelValue="updateField('username', $event)"
        />
      </div>
      <div class="auth-field">
        <span class="auth-label">{{ t('http.password', 'Password') }}</span>
        <ValueSourceSelector
          :modelValue="localValue.password || ''"
          inputType="password"
          :placeholder="t('http.password', 'Password')"
          :readonly="readOnly"
          :uiInputFields="uiInputFields"
          :previousSteps="previousSteps"
          @update:modelValue="updateField('password', $event)"
        />
      </div>
    </div>

    <!-- API Key Fields -->
    <div v-if="authType === 'api_key'" class="auth-fields">
      <div class="auth-field">
        <span class="auth-label">{{ t('http.headerName', 'Header Name') }}</span>
        <AppInput
          :modelValue="localValue.header_name || 'X-API-Key'"
          :readonly="readOnly"
          @update:modelValue="updateField('header_name', $event)"
          size="sm"
        />
      </div>
      <div class="auth-field">
        <span class="auth-label">{{ t('http.apiKey', 'API Key') }}</span>
        <ValueSourceSelector
          :modelValue="localValue.api_key || ''"
          inputType="password"
          :placeholder="t('http.apiKey', 'API Key')"
          :readonly="readOnly"
          :uiInputFields="uiInputFields"
          :previousSteps="previousSteps"
          @update:modelValue="updateField('api_key', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AppInput from '@/components/common/AppInput.vue'
import ValueSourceSelector from '../../ValueSourceSelector.vue'

const { t } = useI18n()
let ignoreUntil = 0

const props = defineProps({
  modelValue: { type: Object, default: null },
  readOnly: { type: Boolean, default: false },
  uiInputFields: { type: Array, default: () => [] },
  previousSteps: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue'])

const authType = ref('none')
const localValue = ref({})

function parseModelValue(val) {
  if (!val || typeof val !== 'object') {
    authType.value = 'none'
    localValue.value = {}
    return
  }
  authType.value = val.type || 'none'
  localValue.value = { ...val }
}

watch(() => props.modelValue, (val) => {
  if (Date.now() < ignoreUntil) return
  parseModelValue(val)
}, { immediate: true, deep: true })

function emitUpdate() {
  ignoreUntil = Date.now() + 1000
  if (authType.value === 'none') {
    emit('update:modelValue', null)
    return
  }
  emit('update:modelValue', { ...localValue.value, type: authType.value })
}

function onTypeChange(type) {
  authType.value = type
  // Reset fields for the new type
  if (type === 'none') {
    localValue.value = {}
  } else if (type === 'bearer') {
    localValue.value = { type: 'bearer', token: localValue.value.token || '' }
  } else if (type === 'basic') {
    localValue.value = { type: 'basic', username: localValue.value.username || '', password: localValue.value.password || '' }
  } else if (type === 'api_key') {
    localValue.value = { type: 'api_key', header_name: localValue.value.header_name || 'X-API-Key', api_key: localValue.value.api_key || '' }
  }
  emitUpdate()
}

function updateField(field, value) {
  localValue.value[field] = value
  emitUpdate()
}
</script>

<style scoped>
.auth-config-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.auth-fields {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px;
  background: rgba(15, 23, 42, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
}

.auth-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.auth-label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.auth-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(7, 11, 20, 0.9) 100%);
  color: #e2e8f0;
  font-size: 13px;
  transition: all 0.2s;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 32px;
}

.auth-select:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.15);
}

.auth-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-select option {
  background: #0f172a;
  color: #e2e8f0;
}

.auth-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(7, 11, 20, 0.9) 100%);
  color: #e2e8f0;
  font-size: 13px;
  transition: all 0.2s;
  box-sizing: border-box;
}

.auth-input:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.15);
}

.auth-input::placeholder {
  color: #475569;
}

.auth-input[readonly] {
  opacity: 0.7;
  cursor: default;
}
</style>
