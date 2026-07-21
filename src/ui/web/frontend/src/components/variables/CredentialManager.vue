<template>
  <div class="bg-gray-800 rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700">
      <div class="flex items-center gap-2">
        <Key :size="18" class="text-purple-400" />
        <h3 class="text-sm font-medium text-white">{{ $t('variables.credentials') }}</h3>
        <span v-if="credentials.length" class="text-xs text-gray-500">({{ credentials.length }})</span>
      </div>
      <button
        @click="showCreateModal = true"
        class="flex items-center gap-1 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg transition-colors"
      >
        <Plus :size="14" />
        {{ $t('common.create') }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="p-8 flex items-center justify-center">
      <Loader :size="24" class="text-purple-400 animate-spin" />
    </div>

    <!-- Empty State -->
    <div v-else-if="!credentials.length" class="p-8 text-center text-gray-400">
      <Key :size="32" class="mx-auto mb-2 opacity-50" />
      <p>{{ $t('variables.noCredentials') }}</p>
    </div>

    <!-- Credentials List -->
    <div v-else class="divide-y divide-gray-700 max-h-96 overflow-y-auto">
      <div
        v-for="credential in credentials"
        :key="credential.id"
        class="p-4"
      >
        <div class="flex items-center justify-between">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-white">{{ credential.name }}</span>
              <span
                v-if="credential.credential_type && credential.credential_type !== 'generic'"
                class="text-xs px-1.5 py-0.5 bg-purple-900/50 text-purple-300 rounded"
              >
                {{ typeLabel(credential.credential_type) }}
              </span>
            </div>
            <p class="text-xs text-gray-500 mt-0.5">
              {{ $t(`variables.scopes.${credential.scope}`) }}
              <span v-if="credential.lastAccessed">
                - Last accessed: {{ formatDate(credential.lastAccessed) }}
              </span>
            </p>
          </div>
          <div class="flex items-center gap-2">
            <!-- Masked Value -->
            <code class="text-xs text-gray-500 bg-gray-900 px-2 py-1 rounded">
              {{ revealedValues[credential.id] || '••••••••' }}
            </code>

            <!-- Reveal Button -->
            <button
              v-if="!revealedValues[credential.id]"
              @click="handleReveal(credential)"
              aria-label="Reveal value"
              class="p-1.5 text-gray-400 hover:text-purple-400 transition-colors"
              :title="$t('variables.reveal')"
            >
              <Eye :size="14" />
            </button>
            <button
              v-else
              @click="hideValue(credential.id)"
              aria-label="Hide value"
              class="p-1.5 text-gray-400 hover:text-gray-300 transition-colors"
            >
              <EyeOff :size="14" />
            </button>

            <!-- Copy -->
            <button
              v-if="revealedValues[credential.id]"
              @click="copyValue(credential.id)"
              aria-label="Copy value"
              class="p-1.5 text-gray-400 hover:text-white transition-colors"
            >
              <Copy :size="14" />
            </button>

            <!-- Delete -->
            <button
              @click="handleDelete(credential)"
              aria-label="Delete credential"
              class="p-1.5 text-gray-400 hover:text-red-400 transition-colors"
            >
              <Trash2 :size="14" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showCreateModal = false"
    >
      <div class="bg-gray-800 rounded-lg w-full max-w-md mx-4">
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <h3 class="text-sm font-medium text-white">{{ $t('credentials.createTitle') }}</h3>
          <button @click="showCreateModal = false" aria-label="Close" class="p-1 text-gray-400 hover:text-white">
            <X :size="18" />
          </button>
        </div>
        <form @submit.prevent="handleCreate" class="p-4 space-y-4">
          <!-- Name -->
          <div>
            <label class="block text-xs text-gray-500 mb-1">Name *</label>
            <AppInput
              v-model="createForm.name"
              required
            />
          </div>

          <!-- Type Selector -->
          <div>
            <label class="block text-xs text-gray-500 mb-1">Type</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="(schema, typeKey) in typeSchemas"
                :key="typeKey"
                type="button"
                @click="createForm.credential_type = typeKey"
                class="px-3 py-1.5 text-xs rounded-lg border transition-colors"
                :class="createForm.credential_type === typeKey
                  ? 'border-purple-500 bg-purple-600/20 text-purple-300'
                  : 'border-gray-600 text-gray-400 hover:border-gray-500'"
              >
                {{ schema.label }}
              </button>
            </div>
            <p v-if="currentSchema" class="text-xs text-gray-500 mt-1">
              {{ currentSchema.description }}
            </p>
          </div>

          <!-- Dynamic Fields -->
          <div v-for="field in currentFields" :key="field.name">
            <label class="block text-xs text-gray-500 mb-1">
              {{ field.label }} {{ field.required ? '*' : '' }}
            </label>
            <AppInput
              v-model="createForm.fields[field.name]"
              :type="field.type"
              :placeholder="field.placeholder"
              :required="field.required"
            />
          </div>

          <div class="flex gap-2">
            <button
              type="button"
              @click="showCreateModal = false"
              class="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg"
            >
              {{ $t('common.cancel') }}
            </button>
            <button
              type="submit"
              class="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg"
            >
              {{ $t('common.create') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Reveal Modal -->
    <div
      v-if="showRevealModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showRevealModal = false"
    >
      <div class="bg-gray-800 rounded-lg w-full max-w-md mx-4">
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <h3 class="text-sm font-medium text-white">{{ $t('variables.reveal') }}</h3>
          <button @click="showRevealModal = false" aria-label="Close" class="p-1 text-gray-400 hover:text-white">
            <X :size="18" />
          </button>
        </div>
        <form @submit.prevent="confirmReveal" class="p-4 space-y-4">
          <div>
            <label class="block text-xs text-gray-500 mb-1">{{ $t('variables.revealReason') }} *</label>
            <AppTextarea
              v-model="revealReason"
              :rows="3"
              :placeholder="$t('variables.revealReasonPlaceholder')"
            />
          </div>
          <div class="flex gap-2">
            <button
              type="button"
              @click="showRevealModal = false"
              class="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg"
            >
              {{ $t('common.cancel') }}
            </button>
            <button
              type="submit"
              class="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg"
            >
              {{ $t('variables.reveal') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Key,
  Plus,
  Loader,
  Eye,
  EyeOff,
  Copy,
  Trash2,
  X
} from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'

const DEFAULT_TYPE_SCHEMAS = {
  api_key: { label: 'API Key', description: 'A single API key or token', fields: [{ name: 'value', label: 'API Key', type: 'password', required: true, placeholder: 'sk-...' }] },
  bearer_token: { label: 'Bearer Token', description: 'OAuth Bearer token', fields: [{ name: 'value', label: 'Token', type: 'password', required: true, placeholder: 'xoxb-... or ghp_...' }] },
  basic_auth: { label: 'Basic Auth', description: 'Username and password', fields: [{ name: 'username', label: 'Username', type: 'text', required: true, placeholder: 'user@flyto2.com' }, { name: 'password', label: 'Password', type: 'password', required: true, placeholder: '' }] },
  oauth2: { label: 'OAuth2', description: 'OAuth2 client credentials', fields: [{ name: 'client_id', label: 'Client ID', type: 'text', required: true, placeholder: '' }, { name: 'client_secret', label: 'Client Secret', type: 'password', required: true, placeholder: '' }, { name: 'token_url', label: 'Token URL', type: 'text', required: false, placeholder: 'https://oauth.flyto2.com/token' }, { name: 'scopes', label: 'Scopes', type: 'text', required: false, placeholder: 'read write' }] },
  generic: { label: 'Generic', description: 'Free-form secret value', fields: [{ name: 'value', label: 'Value', type: 'password', required: true, placeholder: '' }] },
}

const props = defineProps({
  credentials: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  typeSchemas: {
    type: Object,
    default: () => null
  }
})

const emit = defineEmits(['create', 'reveal', 'delete'])
const { t } = useI18n()

const showCreateModal = ref(false)
const showRevealModal = ref(false)
const revealingCredential = ref(null)
const revealReason = ref('')
const revealedValues = ref({})
const createForm = ref({ name: '', credential_type: 'generic', fields: {} })

const schemas = computed(() => props.typeSchemas || DEFAULT_TYPE_SCHEMAS)

const currentSchema = computed(() => schemas.value[createForm.value.credential_type])
const currentFields = computed(() => currentSchema.value?.fields || [])

// Reset fields when type changes
watch(() => createForm.value.credential_type, () => {
  createForm.value.fields = {}
})

function typeLabel(type) {
  const s = schemas.value[type]
  return s ? s.label : type
}

function handleReveal(credential) {
  revealingCredential.value = credential
  revealReason.value = ''
  showRevealModal.value = true
}

async function confirmReveal() {
  if (!revealingCredential.value || !revealReason.value) return

  emit('reveal', {
    id: revealingCredential.value.id,
    reason: revealReason.value,
    callback: (value) => {
      revealedValues.value[revealingCredential.value.id] = value
      showRevealModal.value = false
      // Auto-hide after 30 seconds
      setTimeout(() => {
        hideValue(revealingCredential.value.id)
      }, 30000)
    }
  })
}

function hideValue(id) {
  delete revealedValues.value[id]
}

async function copyValue(id) {
  const value = revealedValues.value[id]
  if (value) {
    await navigator.clipboard.writeText(value)
  }
}

function handleCreate() {
  emit('create', {
    name: createForm.value.name,
    credential_type: createForm.value.credential_type,
    fields: { ...createForm.value.fields },
  })
  createForm.value = { name: '', credential_type: 'generic', fields: {} }
  showCreateModal.value = false
}

function handleDelete(credential) {
  emit('delete', credential)
}

function formatDate(date) {
  return new Date(date).toLocaleDateString()
}
</script>
