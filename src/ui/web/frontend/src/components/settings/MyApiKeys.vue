<template>
  <div class="group relative bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:border-amber-500/30 transition-all duration-500">
    <div class="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
    <div class="relative">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
            <KeyRound :size="20" class="text-white" />
          </div>
          <div>
            <h2 class="text-lg font-semibold text-white">{{ $t('userSettings.apiKeys') }}</h2>
            <p class="text-sm text-gray-400">{{ $t('userSettings.apiKeysDesc') }}</p>
          </div>
        </div>
        <button
          @click="showCreateModal = true"
          class="flex items-center gap-2 px-4 py-2 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-lg hover:bg-amber-500/30 transition-colors text-sm"
        >
          <Plus :size="16" />
          {{ $t('userSettings.createApiKey') }}
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-12">
        <Loader2 :size="24" class="animate-spin text-amber-400" />
      </div>

      <!-- No API Keys -->
      <div v-else-if="apiKeys.length === 0" class="text-center py-12">
        <div class="w-16 h-16 rounded-2xl bg-gray-700/50 flex items-center justify-center mx-auto mb-4">
          <KeyRound :size="32" class="text-gray-500" />
        </div>
        <p class="text-gray-400 mb-4">{{ $t('userSettings.noApiKeys') }}</p>
        <p class="text-sm text-gray-500 max-w-sm mx-auto">
          {{ $t('userSettings.noApiKeysDesc') }}
        </p>
      </div>

      <!-- API Keys List -->
      <div v-else class="space-y-4">
        <div
          v-for="apiKey in apiKeys"
          :key="apiKey.id"
          class="p-4 bg-gray-900/50 border border-white/10 rounded-xl hover:border-amber-500/30 transition-all"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-3 mb-2">
                <span class="text-white font-medium">{{ apiKey.name }}</span>
                <span
                  :class="[
                    'px-2.5 py-0.5 text-xs font-medium rounded-full',
                    apiKey.isActive
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-red-500/20 text-red-400'
                  ]"
                >
                  {{ apiKey.isActive ? $t('userSettings.apiKeyStatus.active') : $t('userSettings.apiKeyStatus.revoked') }}
                </span>
              </div>
              <div class="text-sm font-mono text-gray-400 truncate mb-2">
                {{ apiKey.keyPrefix }}{{ '•'.repeat(24) }}
              </div>
              <div class="flex items-center gap-4 text-sm text-gray-500">
                <span class="flex items-center gap-1">
                  <Calendar :size="14" />
                  {{ $t('userSettings.created') }}: {{ formatDate(apiKey.createdAt) }}
                </span>
                <span v-if="apiKey.lastUsedAt" class="flex items-center gap-1">
                  <Clock :size="14" />
                  {{ $t('userSettings.lastUsed') }}: {{ formatDate(apiKey.lastUsedAt) }}
                </span>
                <span v-if="apiKey.expiresAt" class="flex items-center gap-1">
                  <AlertCircle :size="14" :class="isExpired(apiKey.expiresAt) ? 'text-red-400' : ''" />
                  {{ $t('userSettings.expires') }}: {{ formatDate(apiKey.expiresAt) }}
                </span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="apiKey.isActive"
                @click="confirmRevoke(apiKey)"
                :disabled="revokingId === apiKey.id"
                class="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all disabled:opacity-50"
                :title="$t('userSettings.revokeApiKey')"
              >
                <Loader2 v-if="revokingId === apiKey.id" :size="18" class="animate-spin" />
                <Ban v-else :size="18" />
              </button>
              <button
                @click="confirmDelete(apiKey)"
                :disabled="deletingId === apiKey.id"
                class="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all disabled:opacity-50"
                :title="$t('userSettings.deleteApiKey')"
              >
                <Loader2 v-if="deletingId === apiKey.id" :size="18" class="animate-spin" />
                <Trash2 v-else :size="18" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="errorMessage" class="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
        <AlertCircle :size="16" />
        {{ errorMessage }}
      </div>
    </div>

    <!-- Create API Key Modal -->
    <Teleport to="body">
      <div
        v-if="showCreateModal"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        @click.self="closeCreateModal"
      >
        <div class="bg-gray-800 rounded-2xl border border-white/10 w-full max-w-md overflow-hidden">
          <!-- Header -->
          <div class="p-6 border-b border-white/10">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
                  <KeyRound :size="20" class="text-white" />
                </div>
                <div>
                  <h3 class="text-lg font-semibold text-white">{{ $t('userSettings.createApiKey') }}</h3>
                  <p class="text-sm text-gray-400">{{ $t('userSettings.createApiKeyDesc') }}</p>
                </div>
              </div>
              <button
                @click="closeCreateModal"
                aria-label="Close"
                class="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-all"
              >
                <X :size="20" />
              </button>
            </div>
          </div>

          <!-- Content -->
          <div class="p-6">
            <form @submit.prevent="createApiKey">
              <div class="space-y-4">
                <!-- Name -->
                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">
                    {{ $t('userSettings.apiKeyName') }} *
                  </label>
                  <AppInput
                    v-model="createForm.name"
                    :placeholder="$t('userSettings.apiKeyNamePlaceholder')"
                  />
                </div>

                <!-- Expiration -->
                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">
                    {{ $t('userSettings.apiKeyExpiration') }}
                  </label>
                  <AppSelect
                    v-model="createForm.expiresIn"
                    :options="[
                      { value: 'never', label: $t('userSettings.expirationOptions.never') },
                      { value: '30', label: $t('userSettings.expirationOptions.30days') },
                      { value: '90', label: $t('userSettings.expirationOptions.90days') },
                      { value: '180', label: $t('userSettings.expirationOptions.180days') },
                      { value: '365', label: $t('userSettings.expirationOptions.1year') }
                    ]"
                  />
                </div>

                <!-- Scopes (optional) -->
                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">
                    {{ $t('userSettings.apiKeyScopes') }}
                  </label>
                  <div class="space-y-2">
                    <label class="flex items-center gap-3 p-3 bg-gray-900/50 border border-white/10 rounded-xl cursor-pointer hover:border-amber-500/30 transition-all">
                      <input
                        v-model="createForm.scopes"
                        type="checkbox"
                        value="read"
                        class="w-4 h-4 text-amber-500 bg-gray-700 border-gray-600 rounded focus:ring-amber-500"
                      />
                      <div>
                        <span class="text-white text-sm">{{ $t('userSettings.scopeOptions.read') }}</span>
                        <p class="text-xs text-gray-500">{{ $t('userSettings.scopeOptions.readDesc') }}</p>
                      </div>
                    </label>
                    <label class="flex items-center gap-3 p-3 bg-gray-900/50 border border-white/10 rounded-xl cursor-pointer hover:border-amber-500/30 transition-all">
                      <input
                        v-model="createForm.scopes"
                        type="checkbox"
                        value="write"
                        class="w-4 h-4 text-amber-500 bg-gray-700 border-gray-600 rounded focus:ring-amber-500"
                      />
                      <div>
                        <span class="text-white text-sm">{{ $t('userSettings.scopeOptions.write') }}</span>
                        <p class="text-xs text-gray-500">{{ $t('userSettings.scopeOptions.writeDesc') }}</p>
                      </div>
                    </label>
                    <label class="flex items-center gap-3 p-3 bg-gray-900/50 border border-white/10 rounded-xl cursor-pointer hover:border-amber-500/30 transition-all">
                      <input
                        v-model="createForm.scopes"
                        type="checkbox"
                        value="execute"
                        class="w-4 h-4 text-amber-500 bg-gray-700 border-gray-600 rounded focus:ring-amber-500"
                      />
                      <div>
                        <span class="text-white text-sm">{{ $t('userSettings.scopeOptions.execute') }}</span>
                        <p class="text-xs text-gray-500">{{ $t('userSettings.scopeOptions.executeDesc') }}</p>
                      </div>
                    </label>
                  </div>
                </div>
              </div>

              <!-- Error -->
              <div v-if="createError" class="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {{ createError }}
              </div>

              <!-- Actions -->
              <div class="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  @click="closeCreateModal"
                  class="px-4 py-2 text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                >
                  {{ $t('common.cancel') }}
                </button>
                <button
                  type="submit"
                  :disabled="creating || !createForm.name.trim()"
                  class="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Loader2 v-if="creating" :size="16" class="animate-spin" />
                  {{ $t('userSettings.createApiKey') }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Show New API Key Modal -->
    <Teleport to="body">
      <div
        v-if="showNewKeyModal"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      >
        <div class="bg-gray-800 rounded-2xl border border-white/10 w-full max-w-md overflow-hidden">
          <!-- Header -->
          <div class="p-6 border-b border-white/10">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
                <Check :size="20" class="text-white" />
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ $t('userSettings.apiKeyCreated') }}</h3>
                <p class="text-sm text-gray-400">{{ $t('userSettings.apiKeyCreatedDesc') }}</p>
              </div>
            </div>
          </div>

          <!-- Content -->
          <div class="p-6">
            <div class="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl mb-4">
              <div class="flex items-start gap-3">
                <AlertCircle :size="20" class="text-amber-400 flex-shrink-0 mt-0.5" />
                <div class="text-sm text-amber-200">
                  {{ $t('userSettings.apiKeyWarning') }}
                </div>
              </div>
            </div>

            <div class="relative">
              <label class="block text-sm font-medium text-gray-300 mb-2">{{ $t('userSettings.yourApiKey') }}</label>
              <div class="flex items-center gap-2">
                <AppInput
                  :modelValue="newApiKey"
                  readonly
                  class="flex-1"
                />
                <button
                  @click="copyApiKey"
                  aria-label="Copy API key"
                  class="p-3 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-xl hover:bg-amber-500/30 transition-colors"
                  :title="$t('common.copy')"
                >
                  <Copy :size="18" />
                </button>
              </div>
              <p v-if="copied" class="text-xs text-emerald-400 mt-2">{{ $t('common.copied') }}</p>
            </div>

            <!-- Close Button -->
            <div class="mt-6 flex justify-end">
              <button
                @click="closeNewKeyModal"
                class="px-4 py-2 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-colors"
              >
                {{ $t('common.done') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Revoke Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="showRevokeModal"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        @click.self="showRevokeModal = false"
      >
        <div class="bg-gray-800 rounded-2xl border border-white/10 w-full max-w-sm overflow-hidden">
          <div class="p-6">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center">
                <AlertTriangle :size="20" class="text-red-400" />
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ $t('userSettings.revokeApiKeyTitle') }}</h3>
              </div>
            </div>
            <p class="text-gray-400 text-sm mb-4">
              {{ $t('userSettings.revokeApiKeyDesc', { name: revokeTarget?.name }) }}
            </p>
            <div class="flex justify-end gap-3">
              <button
                @click="showRevokeModal = false"
                class="px-4 py-2 text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              >
                {{ $t('common.cancel') }}
              </button>
              <button
                @click="revokeApiKey"
                :disabled="revokingId"
                class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                <Loader2 v-if="revokingId" :size="16" class="animate-spin" />
                {{ $t('userSettings.revokeApiKey') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="showDeleteModal"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        @click.self="showDeleteModal = false"
      >
        <div class="bg-gray-800 rounded-2xl border border-white/10 w-full max-w-sm overflow-hidden">
          <div class="p-6">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center">
                <AlertTriangle :size="20" class="text-red-400" />
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ $t('userSettings.deleteApiKeyTitle') }}</h3>
              </div>
            </div>
            <p class="text-gray-400 text-sm mb-4">
              {{ $t('userSettings.deleteApiKeyDesc', { name: deleteTarget?.name }) }}
            </p>
            <div class="flex justify-end gap-3">
              <button
                @click="showDeleteModal = false"
                class="px-4 py-2 text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              >
                {{ $t('common.cancel') }}
              </button>
              <button
                @click="deleteApiKey"
                :disabled="deletingId"
                class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                <Loader2 v-if="deletingId" :size="16" class="animate-spin" />
                {{ $t('userSettings.deleteApiKey') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import { apiKeysAPI } from '@/api/apiKeys'
import {
  KeyRound,
  Plus,
  Loader2,
  Calendar,
  Clock,
  AlertCircle,
  AlertTriangle,
  X,
  Trash2,
  Ban,
  Copy,
  Check
} from 'lucide-vue-next'

const { t } = useI18n()

// State
const loading = ref(true)
const apiKeys = ref([])
const errorMessage = ref('')

// Create modal state
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref('')
const createForm = ref({
  name: '',
  expiresIn: 'never',
  scopes: ['read', 'write', 'execute']
})

// New key modal state
const showNewKeyModal = ref(false)
const newApiKey = ref('')
const copied = ref(false)

// Revoke state
const showRevokeModal = ref(false)
const revokeTarget = ref(null)
const revokingId = ref(null)

// Delete state
const showDeleteModal = ref(false)
const deleteTarget = ref(null)
const deletingId = ref(null)

// Load API keys
async function loadApiKeys() {
  loading.value = true
  errorMessage.value = ''

  const result = await apiKeysAPI.list()
  if (result.ok) {
    apiKeys.value = result.apiKeys
  } else {
    apiKeys.value = []
    errorMessage.value = result.error
  }
  loading.value = false
}

// Create API key
async function createApiKey() {
  if (!createForm.value.name.trim() || creating.value) return

  creating.value = true
  createError.value = ''

  const payload = {
    name: createForm.value.name.trim(),
    scopes: createForm.value.scopes
  }

  if (createForm.value.expiresIn !== 'never') {
    const days = parseInt(createForm.value.expiresIn)
    const expiresAt = new Date()
    expiresAt.setDate(expiresAt.getDate() + days)
    payload.expiresAt = expiresAt.toISOString()
  }

  const result = await apiKeysAPI.create(payload)

  if (result.ok) {
    newApiKey.value = result.apiKey
    showCreateModal.value = false
    showNewKeyModal.value = true
    resetCreateForm()
    await loadApiKeys()
  } else {
    createError.value = result.error
  }
  creating.value = false
}

// Close create modal
function closeCreateModal() {
  showCreateModal.value = false
  resetCreateForm()
}

// Reset create form
function resetCreateForm() {
  createForm.value = {
    name: '',
    expiresIn: 'never',
    scopes: ['read', 'write', 'execute']
  }
  createError.value = ''
}

// Close new key modal
function closeNewKeyModal() {
  showNewKeyModal.value = false
  newApiKey.value = ''
  copied.value = false
}

// Copy API key
async function copyApiKey() {
  try {
    await navigator.clipboard.writeText(newApiKey.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
  }
}

// Confirm revoke
function confirmRevoke(apiKey) {
  revokeTarget.value = apiKey
  showRevokeModal.value = true
}

// Revoke API key
async function revokeApiKey() {
  if (!revokeTarget.value || revokingId.value) return

  revokingId.value = revokeTarget.value.id

  const result = await apiKeysAPI.revoke(revokeTarget.value.id)

  if (result.ok) {
    await loadApiKeys()
    showRevokeModal.value = false
    revokeTarget.value = null
  } else {
    errorMessage.value = result.error
  }
  revokingId.value = null
}

// Confirm delete
function confirmDelete(apiKey) {
  deleteTarget.value = apiKey
  showDeleteModal.value = true
}

// Delete API key
async function deleteApiKey() {
  if (!deleteTarget.value || deletingId.value) return

  deletingId.value = deleteTarget.value.id

  const result = await apiKeysAPI.delete(deleteTarget.value.id)

  if (result.ok) {
    await loadApiKeys()
    showDeleteModal.value = false
    deleteTarget.value = null
  } else {
    errorMessage.value = result.error
  }
  deletingId.value = null
}

// Helper functions
function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

function isExpired(dateStr) {
  if (!dateStr) return false
  return new Date(dateStr) < new Date()
}

onMounted(() => {
  loadApiKeys()
})
</script>
