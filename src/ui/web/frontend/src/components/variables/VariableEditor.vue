<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    @click.self="$emit('close')"
  >
    <div class="bg-gray-800 rounded-lg w-full max-w-md mx-4">
      <!-- Header -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <h3 class="text-sm font-medium text-white">
          {{ variable ? $t('variables.edit') : $t('variables.create') }}
        </h3>
        <button
          @click="$emit('close')"
          aria-label="Close"
          class="p-1 text-gray-400 hover:text-white transition-colors"
        >
          <X :size="18" />
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="p-4 space-y-4">
        <!-- Name -->
        <div>
          <label class="block text-xs text-gray-500 mb-1">
            {{ $t('variables.name') }} *
          </label>
          <AppInput
            v-model="form.name"
            required
            :placeholder="$t('variables.name')"
          />
        </div>

        <!-- Type -->
        <div>
          <label class="block text-xs text-gray-500 mb-1">
            {{ $t('variables.type') }} *
          </label>
          <AppSelect
            v-model="form.type"
            :options="[
              { value: 'string', label: $t('variables.types.string') },
              { value: 'number', label: $t('variables.types.number') },
              { value: 'boolean', label: $t('variables.types.boolean') },
              { value: 'json', label: $t('variables.types.json') },
              { value: 'secret', label: $t('variables.types.secret') }
            ]"
          />
        </div>

        <!-- Value -->
        <div>
          <label class="block text-xs text-gray-500 mb-1">
            {{ $t('variables.value') }} *
          </label>
          <!-- String/Secret -->
          <AppInput
            v-if="form.type === 'string' || form.type === 'secret'"
            v-model="form.value"
            :type="form.type === 'secret' ? 'password' : 'text'"
            required
          />
          <!-- Number -->
          <input
            v-else-if="form.type === 'number'"
            v-model.number="form.value"
            type="number"
            required
            class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm text-white focus:outline-none focus:border-purple-500"
          />
          <!-- Boolean -->
          <AppSelect
            v-else-if="form.type === 'boolean'"
            v-model="form.value"
            :options="[
              { value: true, label: $t('common.yes') },
              { value: false, label: $t('common.no') }
            ]"
          />
          <!-- JSON -->
          <AppTextarea
            v-else-if="form.type === 'json'"
            v-model="form.value"
            :rows="4"
            placeholder='{ "key": "value" }'
          />
          <p v-if="jsonError" class="text-xs text-red-400 mt-1">{{ jsonError }}</p>
        </div>

        <!-- Scope -->
        <div>
          <label class="block text-xs text-gray-500 mb-1">
            {{ $t('variables.scope') }} *
          </label>
          <AppSelect
            v-model="form.scope"
            :options="[
              { value: 'workspace', label: 'Workspace' },
              { value: 'project', label: $t('variables.scopes.project') },
              { value: 'workflow', label: $t('variables.scopes.workflow') }
            ]"
          />
        </div>

        <!-- Scope ID -->
        <div v-if="form.scope !== 'workspace'">
          <label class="block text-xs text-gray-500 mb-1">
            {{ form.scope === 'project' ? 'Project ID' : 'Workflow ID' }} *
          </label>
          <AppInput
            v-model="form.scopeId"
            required
          />
        </div>

        <!-- Environment -->
        <div>
          <label class="block text-xs text-gray-500 mb-1">
            {{ $t('variables.environment') }} *
          </label>
          <AppSelect
            v-model="form.environment"
            :options="[
              { value: 'all', label: $t('variables.environments.all') },
              { value: 'development', label: $t('variables.environments.development') },
              { value: 'staging', label: $t('variables.environments.staging') },
              { value: 'production', label: $t('variables.environments.production') }
            ]"
          />
        </div>

        <!-- Actions -->
        <div class="flex gap-2 pt-2">
          <button
            type="button"
            @click="$emit('close')"
            class="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors"
          >
            {{ $t('common.cancel') }}
          </button>
          <button
            type="submit"
            :disabled="loading || !!jsonError"
            class="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm rounded-lg transition-colors"
          >
            <Loader v-if="loading" :size="16" class="animate-spin" />
            {{ variable ? $t('common.update') : $t('common.create') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { X, Loader } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  variable: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'save'])
const { t } = useI18n()

const form = ref({
  name: '',
  type: 'string',
  value: '',
  scope: 'workspace',
  scopeId: '',
  environment: 'all'
})

// Watch for variable changes (edit mode)
watch(() => props.variable, (v) => {
  if (v) {
    form.value = {
      name: v.name || '',
      type: v.type || 'string',
      value: v.type === 'json' ? JSON.stringify(v.value, null, 2) : v.value,
      scope: v.scope || 'workspace',
      scopeId: v.scopeId || '',
      environment: v.environment || 'all'
    }
  } else {
    form.value = {
      name: '',
      type: 'string',
      value: '',
      scope: 'workspace',
      scopeId: '',
      environment: 'all'
    }
  }
}, { immediate: true })

// JSON validation
const jsonError = computed(() => {
  if (form.value.type !== 'json') return null
  try {
    JSON.parse(form.value.value)
    return null
  } catch {
    return t('debug.invalidJson')
  }
})

function handleSubmit() {
  let value = form.value.value
  if (form.value.type === 'json') {
    value = JSON.parse(form.value.value)
  }

  emit('save', {
    ...form.value,
    value,
    id: props.variable?.id
  })
}
</script>
