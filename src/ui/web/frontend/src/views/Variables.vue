<template>
  <div class="min-h-screen bg-gray-900 p-6">
    <div class="max-w-6xl mx-auto space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-white">{{ $t('variables.title') }}</h1>
          <p class="text-sm text-gray-400 mt-1">{{ $t('variables.subtitle') }}</p>
        </div>
      </div>

      <!-- Environment Tabs -->
      <div class="flex gap-2">
        <button
          v-for="env in environments"
          :key="env"
          @click="switchEnvironment(env)"
          class="px-4 py-2 text-sm rounded-lg transition-colors"
          :class="currentEnvironment === env
            ? 'bg-purple-600 text-white'
            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
        >
          {{ $t(`variables.environments.${env}`) }}
        </button>
      </div>

      <!-- Main Content -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Variables -->
        <VariableList
          :variables="filteredVariables"
          :loading="variableStore.isLoading"
          @create="handleCreateVariable"
          @edit="handleEditVariable"
          @delete="handleDeleteVariable"
        />

        <!-- Credentials -->
        <CredentialManager
          :credentials="credentialStore.credentials"
          :loading="credentialStore.isLoading"
          @create="handleCreateCredential"
          @reveal="handleRevealCredential"
          @delete="handleDeleteCredential"
        />
      </div>

      <!-- Variable Editor Modal -->
      <VariableEditor
        :is-open="showEditor"
        :variable="editingVariable"
        :loading="variableStore.isLoading"
        @close="closeEditor"
        @save="handleSaveVariable"
      />

      <!-- Delete Confirmation -->
      <div
        v-if="showDeleteConfirm"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showDeleteConfirm = false"
      >
        <div class="bg-gray-800 rounded-lg w-full max-w-sm mx-4 p-4">
          <h3 class="text-sm font-medium text-white mb-2">{{ $t('variables.deleteConfirm') }}</h3>
          <p class="text-sm text-gray-400 mb-4">{{ deletingItem?.name }}</p>
          <div class="flex gap-2">
            <button
              @click="showDeleteConfirm = false"
              class="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg"
            >
              {{ $t('common.cancel') }}
            </button>
            <button
              @click="confirmDelete"
              class="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg"
            >
              {{ $t('common.delete') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useVariableStore } from '@/stores/variableStore'
import { useCredentialStore } from '@/stores/credentialStore'
import { VariableList, VariableEditor, CredentialManager } from '@/components/variables'
import { telemetry } from '@/services/telemetry'

const { t } = useI18n()
const variableStore = useVariableStore()
const credentialStore = useCredentialStore()

const environments = ['all', 'development', 'staging', 'production']
const currentEnvironment = ref('all')

const showEditor = ref(false)
const editingVariable = ref(null)
const showDeleteConfirm = ref(false)
const deletingItem = ref(null)
const deleteType = ref('variable') // 'variable' or 'credential'

// Filtered variables by environment
const filteredVariables = computed(() => {
  if (currentEnvironment.value === 'all') {
    return variableStore.variables
  }
  return variableStore.variables.filter(v =>
    v.environment === currentEnvironment.value || v.environment === 'all'
  )
})

// Switch environment with tracking
function switchEnvironment(env) {
  if (env === currentEnvironment.value) return
  const oldEnv = currentEnvironment.value
  currentEnvironment.value = env
  telemetry.track('variable.environment_switch', {
    old_environment: oldEnv,
    new_environment: env,
    variable_count: filteredVariables.value.length,
  })
}

// Fetch data on mount
onMounted(async () => {
  await Promise.all([
    variableStore.fetchVariables(),
    credentialStore.fetchCredentials()
  ])
})

// Variable handlers
function handleCreateVariable() {
  editingVariable.value = null
  showEditor.value = true
}

function handleEditVariable(variable) {
  editingVariable.value = variable
  showEditor.value = true
}

function handleDeleteVariable(variable) {
  deletingItem.value = variable
  deleteType.value = 'variable'
  showDeleteConfirm.value = true
}

async function handleSaveVariable(data) {
  if (data.id) {
    await variableStore.updateVariable(data.id, data)
  } else {
    await variableStore.createVariable(data)
  }
  closeEditor()
}

function closeEditor() {
  showEditor.value = false
  editingVariable.value = null
}

// Credential handlers
async function handleCreateCredential(data) {
  await credentialStore.createCredential(data)
}

async function handleRevealCredential({ id, reason, callback }) {
  const result = await credentialStore.revealCredential(id, reason)
  if (result.ok && callback) {
    callback(result.value)
  }
}

function handleDeleteCredential(credential) {
  deletingItem.value = credential
  deleteType.value = 'credential'
  showDeleteConfirm.value = true
}

// Delete confirmation
async function confirmDelete() {
  if (deleteType.value === 'variable') {
    await variableStore.deleteVariable(deletingItem.value.id)
  } else {
    await credentialStore.deleteCredential(deletingItem.value.id)
  }
  showDeleteConfirm.value = false
  deletingItem.value = null
}
</script>
