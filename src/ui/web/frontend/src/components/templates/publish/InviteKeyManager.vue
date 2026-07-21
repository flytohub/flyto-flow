<template>
  <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-5 hover:border-amber-500/30 transition-all duration-500 space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/20">
          <Key :size="16" class="text-white" />
        </div>
        <h4 class="font-semibold text-white">{{ $t('inviteKeys.manageKeys') }}</h4>
      </div>
      <button
        @click="showCreateForm = !showCreateForm"
        class="group flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg transition-all duration-300"
        :class="showCreateForm
          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
          : 'text-gray-400 hover:text-amber-400 hover:bg-amber-500/10'"
      >
        <Plus :size="16" :class="showCreateForm ? 'rotate-45' : ''" class="transition-transform duration-300" />
        {{ showCreateForm ? $t('common.cancel') : $t('inviteKeys.createNew') }}
      </button>
    </div>

    <!-- Create Form -->
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 -translate-y-2 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 -translate-y-2 scale-95"
    >
      <div v-if="showCreateForm" class="relative">
        <div class="absolute -inset-0.5 bg-gradient-to-r from-amber-500/20 to-orange-500/20 rounded-xl blur opacity-75"></div>
        <div class="relative p-4 bg-gray-900/80 backdrop-blur-sm rounded-xl border border-amber-500/20">
          <div class="grid grid-cols-2 gap-3">
            <!-- Max Uses -->
            <div>
              <label class="block text-xs font-medium text-gray-400 mb-1.5">
                {{ $t('inviteKeys.maxUses') }}
              </label>
              <AppSelect
                v-model="newKeyForm.maxUses"
                :options="[
                  { value: 1, label: $t('inviteKeys.usesCount', { count: 1 }) },
                  { value: 5, label: $t('inviteKeys.usesCount', { count: 5 }) },
                  { value: 10, label: $t('inviteKeys.usesCount', { count: 10 }) },
                  { value: 50, label: $t('inviteKeys.usesCount', { count: 50 }) },
                  { value: 100, label: $t('inviteKeys.usesCount', { count: 100 }) },
                  { value: 999, label: $t('inviteKeys.unlimited') }
                ]"
              />
            </div>

            <!-- Expires In -->
            <div>
              <label class="block text-xs font-medium text-gray-400 mb-1.5">
                {{ $t('inviteKeys.expiresIn') }}
              </label>
              <AppSelect
                v-model="newKeyForm.expiresInDays"
                :options="[
                  { value: null, label: $t('inviteKeys.noExpiration') },
                  { value: 1, label: '1 ' + $t('inviteKeys.day') },
                  { value: 7, label: '7 ' + $t('inviteKeys.days') },
                  { value: 30, label: '30 ' + $t('inviteKeys.days') },
                  { value: 90, label: '90 ' + $t('inviteKeys.days') }
                ]"
              />
            </div>
          </div>

          <!-- Note -->
          <div class="mt-3">
            <label class="block text-xs font-medium text-gray-400 mb-1.5">
              {{ $t('inviteKeys.note') }} <span class="text-gray-500">({{ $t('common.optional') }})</span>
            </label>
            <AppInput
              v-model="newKeyForm.note"
              maxlength="200"
              :placeholder="$t('inviteKeys.notePlaceholder')"
            />
          </div>

          <!-- Create Button -->
          <button
            @click="createKey"
            :disabled="isCreating"
            class="mt-4 w-full py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-white font-medium rounded-lg transition-all duration-300 hover:shadow-lg hover:shadow-amber-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <Loader2 v-if="isCreating" :size="16" class="animate-spin" />
            <Sparkles v-else :size="16" />
            {{ $t('inviteKeys.create') }}
          </button>
        </div>
      </div>
    </Transition>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-8">
      <div class="relative">
        <div class="w-10 h-10 border-2 border-amber-500/20 rounded-full"></div>
        <div class="absolute top-0 left-0 w-10 h-10 border-2 border-transparent border-t-amber-500 rounded-full animate-spin"></div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="activeKeys.length === 0 && !showCreateForm" class="text-center py-6">
      <div class="w-12 h-12 bg-gray-800/50 rounded-xl flex items-center justify-center mx-auto mb-3 border border-white/5">
        <Key :size="20" class="text-gray-500" />
      </div>
      <p class="text-sm text-gray-400">{{ $t('inviteKeys.noKeys') }}</p>
      <p class="text-xs text-gray-500 mt-1">{{ $t('inviteKeys.noKeysDesc') }}</p>
    </div>

    <!-- Keys List -->
    <div v-if="!loading && activeKeys.length > 0" class="space-y-2">
      <TransitionGroup
        enter-active-class="transition-all duration-300"
        enter-from-class="opacity-0 translate-x-4"
        enter-to-class="opacity-100 translate-x-0"
        leave-active-class="transition-all duration-200"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div
          v-for="key in activeKeys"
          :key="key.id"
          class="group relative"
        >
          <!-- Glow effect on hover -->
          <div class="absolute -inset-0.5 bg-gradient-to-r from-amber-500/20 to-orange-500/20 rounded-2xl blur opacity-0 group-hover:opacity-100 transition-opacity"></div>

          <div class="relative flex gap-3 p-4 rounded-xl border transition-all duration-300 bg-gray-900/80 border-amber-500/20 hover:border-amber-500/40">
            <!-- Left: Key Info -->
            <div class="flex-1 min-w-0 space-y-3">
              <!-- Top: Key Code + Copy -->
              <div class="flex items-center gap-2">
                <div class="flex-1 flex items-center gap-2 px-3 py-2 rounded-lg bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/20">
                  <Key :size="14" class="text-amber-400" />
                  <code class="flex-1 font-mono text-sm tracking-widest text-amber-300">
                    {{ key.key }}
                  </code>
                </div>
                <button
                  @click="copyKey(key.key)"
                  aria-label="Copy key"
                  class="p-2 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 transition-all"
                  :title="$t('common.copy')"
                >
                  <Copy v-if="copiedKeyId !== key.id" :size="16" />
                  <Check v-else :size="16" class="text-emerald-400" />
                </button>
              </div>

              <!-- Bottom: Stats -->
              <div class="flex items-center gap-3 flex-wrap">
                <!-- Usage -->
                <span class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs text-gray-400 bg-white/5 rounded-lg">
                  <Users :size="12" />
                  {{ key.currentUses }}/{{ key.maxUses >= 999 ? '∞' : key.maxUses }}
                </span>

                <!-- Expiry -->
                <span
                  v-if="key.expiresAt"
                  class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs text-gray-400 bg-white/5 rounded-lg"
                >
                  <Clock :size="12" />
                  {{ formatExpiry(key.expiresAt) }}
                </span>

                <!-- Note -->
                <span
                  v-if="key.note"
                  class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs text-gray-500 bg-white/5 rounded-lg truncate max-w-[150px]"
                  :title="key.note"
                >
                  {{ key.note }}
                </span>
              </div>
            </div>

            <!-- Right: Delete Button -->
            <div class="flex items-center">
              <button
                @click="revokeKey(key)"
                :disabled="revokingKeyId === key.id"
                aria-label="Revoke key"
                class="p-3 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-all disabled:opacity-50"
                :title="$t('inviteKeys.revoke')"
              >
                <Loader2 v-if="revokingKeyId === key.id" :size="18" class="animate-spin" />
                <Trash2 v-else :size="18" />
              </button>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Key, Plus, Copy, Check, Clock, Trash2, Loader2, Sparkles, Users } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import { templatesAPI } from '@/api/templates'

const { t } = useI18n()

const props = defineProps({
  templateId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['keyCreated', 'keyRevoked'])

// State
const loading = ref(false)
const keys = ref([])
const showCreateForm = ref(false)
const isCreating = ref(false)
const copiedKeyId = ref(null)
const revokingKeyId = ref(null)

const newKeyForm = reactive({
  maxUses: 10,
  expiresInDays: null,
  note: ''
})

// Only show active keys
const activeKeys = computed(() => keys.value.filter(k => k.isActive))

// Load keys
async function loadKeys() {
  if (!props.templateId) return

  loading.value = true
  try {
    const result = await templatesAPI.listInviteKeys(props.templateId)
    if (result.ok) {
      keys.value = result.keys || []
    }
  } catch (err) {
  } finally {
    loading.value = false
  }
}

// Create key
async function createKey() {
  if (isCreating.value) return

  isCreating.value = true
  try {
    const result = await templatesAPI.createInviteKey(props.templateId, {
      maxUses: newKeyForm.maxUses,
      expiresInDays: newKeyForm.expiresInDays,
      note: newKeyForm.note || undefined
    })

    if (result.ok) {
      await loadKeys()
      showCreateForm.value = false
      newKeyForm.maxUses = 10
      newKeyForm.expiresInDays = null
      newKeyForm.note = ''
      emit('keyCreated', result.key)
    }
  } catch (err) {
  } finally {
    isCreating.value = false
  }
}

// Copy key
async function copyKey(keyCode) {
  try {
    await navigator.clipboard.writeText(keyCode)
    const key = keys.value.find(k => k.key === keyCode)
    if (key) {
      copiedKeyId.value = key.id
      setTimeout(() => {
        copiedKeyId.value = null
      }, 2000)
    }
  } catch (err) {
  }
}

// Revoke key
async function revokeKey(key) {
  if (revokingKeyId.value) return

  revokingKeyId.value = key.id
  try {
    const result = await templatesAPI.revokeInviteKey(props.templateId, key.id)
    if (result.ok) {
      await loadKeys()
      emit('keyRevoked', key)
    }
  } catch (err) {
  } finally {
    revokingKeyId.value = null
  }
}

// Format expiry date
function formatExpiry(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = date - now

  if (diff < 0) return t('inviteKeys.expired')
  if (diff < 86400000) return Math.floor(diff / 3600000) + 'h'
  if (diff < 604800000) return Math.floor(diff / 86400000) + 'd'
  return date.toLocaleDateString()
}

// Watch for templateId changes (immediate: true handles initial load)
watch(() => props.templateId, (newId) => {
  if (newId) loadKeys()
}, { immediate: true })
</script>
