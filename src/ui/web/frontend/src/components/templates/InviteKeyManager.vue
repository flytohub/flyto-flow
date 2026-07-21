<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      role="dialog"
      aria-modal="true"
      aria-labelledby="invite-keys-modal-title"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      @keydown.esc="close"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/50 backdrop-blur-sm"
        @click="close"
      ></div>

      <!-- Modal -->
      <div class="relative w-full max-w-2xl bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 id="invite-keys-modal-title" class="text-xl font-bold text-gray-900 dark:text-white">{{ $t('inviteKeys.title') }}</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ template?.name || template?.template_name }}
            </p>
          </div>
          <button
            @click="close"
            :aria-label="t('accessibility.closeDialog')"
            class="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
          >
            <X :size="20" aria-hidden="true" />
          </button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          <!-- Create New Key Section -->
          <div class="p-4 bg-gray-50 dark:bg-gray-900 rounded-xl">
            <h3 class="font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <Plus :size="18" />
              {{ $t('inviteKeys.createNew') }}
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">{{ $t('inviteKeys.usageLimit') }}</label>
                <AppSelect
                  v-model="newKey.usageLimit"
                  :options="usageLimitOptions"
                />
              </div>
              <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">{{ $t('inviteKeys.expiresAfter') }}</label>
                <AppSelect
                  v-model="newKey.expiresIn"
                  :options="expirationOptions"
                />
              </div>
            </div>
            <button
              @click="createKey"
              :disabled="isCreating"
              class="mt-4 w-full px-4 py-2.5 min-h-[44px] bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-400"
            >
              <Loader2 v-if="isCreating" :size="18" class="animate-spin" aria-hidden="true" />
              <Key v-else :size="18" aria-hidden="true" />
              {{ isCreating ? $t('inviteKeys.creating') : $t('inviteKeys.generateKey') }}
            </button>
          </div>

          <!-- Newly Created Key -->
          <div
            v-if="newlyCreatedKey"
            class="p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl"
          >
            <div class="flex items-start gap-3">
              <Check :size="20" class="text-emerald-600 mt-0.5" />
              <div class="flex-1">
                <h4 class="font-medium text-emerald-800 dark:text-emerald-300">{{ $t('inviteKeys.keyCreated') }}</h4>
                <p class="text-sm text-emerald-700 dark:text-emerald-400 mt-1">
                  {{ $t('inviteKeys.copyKeyNote') }}
                </p>
                <div class="mt-3 flex items-center gap-2">
                  <code class="flex-1 px-3 py-2 bg-white dark:bg-gray-800 border border-emerald-300 dark:border-emerald-700 rounded-lg text-sm font-mono text-emerald-900 dark:text-emerald-200">
                    {{ newlyCreatedKey }}
                  </code>
                  <button
                    @click="copyKey(newlyCreatedKey)"
                    :aria-label="t('accessibility.copyToClipboard')"
                    class="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400"
                  >
                    <Copy :size="18" aria-hidden="true" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Keys List -->
          <div>
            <h3 class="font-medium text-gray-900 dark:text-white mb-3 flex items-center justify-between">
              <span class="flex items-center gap-2">
                <Key :size="18" />
                {{ $t('inviteKeys.activeKeys') }}
              </span>
              <button
                @click="loadKeys"
                :disabled="isLoading"
                :aria-label="t('accessibility.refreshList')"
                class="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
              >
                <RefreshCw :size="16" :class="{ 'animate-spin': isLoading }" aria-hidden="true" />
              </button>
            </h3>

            <!-- Loading -->
            <div v-if="isLoading" class="py-8 text-center text-gray-400">
              <Loader2 :size="24" class="animate-spin mx-auto" />
              <p class="mt-2 text-sm">{{ $t('inviteKeys.loadingKeys') }}</p>
            </div>

            <!-- Empty State -->
            <div v-else-if="keys.length === 0" class="py-8 text-center">
              <Key :size="32" class="mx-auto text-gray-300 dark:text-gray-600" />
              <p class="mt-2 text-gray-500 dark:text-gray-400">{{ $t('inviteKeys.noKeys') }}</p>
              <p class="text-sm text-gray-400 dark:text-gray-500">{{ $t('inviteKeys.noKeysDesc') }}</p>
            </div>

            <!-- Keys Table -->
            <div v-else class="space-y-3">
              <div
                v-for="key in keys"
                :key="key.keyId"
                :class="[
                  'p-4 rounded-xl border transition-colors',
                  key.revoked
                    ? 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 opacity-60'
                    : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                ]"
              >
                <div class="flex items-start justify-between gap-4">
                  <div class="flex-1 min-w-0">
                    <!-- Key Code -->
                    <div class="flex items-center gap-2">
                      <code class="text-sm font-mono text-gray-700 dark:text-gray-300">
                        {{ maskKey(key.keyCode) }}
                      </code>
                      <span
                        v-if="key.revoked"
                        class="px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-xs rounded-full"
                      >
                        {{ $t('inviteKeys.revoked') }}
                      </span>
                    </div>

                    <!-- Stats -->
                    <div class="flex items-center gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                      <span class="flex items-center gap-1">
                        <Users :size="12" />
                        {{ key.usageLimit
                          ? $t('inviteKeys.usageStats', { used: key.usageCount || 0, limit: key.usageLimit })
                          : $t('inviteKeys.usageUnlimited', { used: key.usageCount || 0 })
                        }}
                      </span>
                      <span v-if="key.expiresAt" class="flex items-center gap-1">
                        <Clock :size="12" />
                        {{ $t('inviteKeys.expires', { date: formatDate(key.expiresAt) }) }}
                      </span>
                      <span v-else class="flex items-center gap-1">
                        <Clock :size="12" />
                        {{ $t('inviteKeys.neverExpires') }}
                      </span>
                    </div>

                    <!-- Created date -->
                    <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
                      {{ $t('inviteKeys.created', { date: formatDate(key.createdAt) }) }}
                    </p>
                  </div>

                  <!-- Actions -->
                  <div class="flex items-center gap-2">
                    <button
                      v-if="!key.revoked"
                      @click="copyKey(key.keyCode)"
                      :aria-label="t('accessibility.copyToClipboard')"
                      class="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
                    >
                      <Copy :size="16" aria-hidden="true" />
                    </button>
                    <button
                      v-if="!key.revoked"
                      @click="confirmRevoke(key)"
                      :aria-label="t('accessibility.revokeKey')"
                      class="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-red-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-500"
                    >
                      <Ban :size="16" aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
          <button
            @click="close"
            class="px-5 py-2.5 min-h-[44px] bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 font-medium rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-500"
          >
            {{ $t('common.close') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Revoke Confirmation Modal -->
  <Teleport to="body">
    <div
      v-if="revokeConfirm.show"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="revoke-confirm-title"
      aria-describedby="revoke-confirm-desc"
      class="fixed inset-0 z-[60] flex items-center justify-center p-4"
      @keydown.esc="revokeConfirm.show = false"
    >
      <div class="absolute inset-0 bg-black/50" @click="revokeConfirm.show = false"></div>
      <div class="relative bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-sm w-full p-6">
        <div class="flex items-start gap-4">
          <div class="p-3 bg-red-100 dark:bg-red-900/30 rounded-full" aria-hidden="true">
            <AlertTriangle :size="24" class="text-red-600 dark:text-red-400" />
          </div>
          <div class="flex-1">
            <h3 id="revoke-confirm-title" class="text-lg font-semibold text-gray-900 dark:text-white">{{ $t('inviteKeys.revokeConfirm.title') }}</h3>
            <p id="revoke-confirm-desc" class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ $t('inviteKeys.revokeConfirm.message') }}
            </p>
            <div class="flex items-center gap-3 mt-4">
              <button
                @click="revokeConfirm.show = false"
                class="flex-1 px-4 py-2 min-h-[44px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 font-medium rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-500"
              >
                {{ $t('common.cancel') }}
              </button>
              <button
                @click="revokeKey"
                :disabled="isRevoking"
                class="flex-1 px-4 py-2 min-h-[44px] bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-400"
              >
                <Loader2 v-if="isRevoking" :size="16" class="animate-spin" aria-hidden="true" />
                {{ isRevoking ? $t('inviteKeys.revoking') : $t('inviteKeys.revokeKey') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { MS_PER_DAY } from '@/constants/time'
import { useToast } from '@/composables/useToast'
import { useRelativeTime } from '@/composables/useRelativeTime'
import {
  X, Key, Plus, Copy, RefreshCw, Loader2, Check, Ban, Users, Clock, AlertTriangle
} from 'lucide-vue-next'
import { templatesAPI } from '@/api/templates'
import AppSelect from '@/components/common/AppSelect.vue'

const { t, locale } = useI18n()
const { showError, success: showSuccess } = useToast()
const { formatRelativeTime } = useRelativeTime()

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  template: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

// Usage limit options with i18n
const usageLimitOptions = computed(() => [
  { value: null, label: t('inviteKeys.unlimited') },
  { value: 1, label: t('inviteKeys.uses', { count: 1 }) },
  { value: 5, label: t('inviteKeys.uses', { count: 5 }) },
  { value: 10, label: t('inviteKeys.uses', { count: 10 }) },
  { value: 50, label: t('inviteKeys.uses', { count: 50 }) },
  { value: 100, label: t('inviteKeys.uses', { count: 100 }) }
])

// Expiration options with i18n
const expirationOptions = computed(() => [
  { value: null, label: t('inviteKeys.never') },
  { value: 7, label: t('inviteKeys.days', { count: 7 }) },
  { value: 30, label: t('inviteKeys.days', { count: 30 }) },
  { value: 90, label: t('inviteKeys.days', { count: 90 }) },
  { value: 365, label: t('inviteKeys.year') }
])

// State
const keys = ref([])
const isLoading = ref(false)
const isCreating = ref(false)
const isRevoking = ref(false)
const newlyCreatedKey = ref(null)

const newKey = reactive({
  usageLimit: null,
  expiresIn: null
})

const revokeConfirm = reactive({
  show: false,
  key: null
})

// Load keys when modal opens
watch(() => props.modelValue, async (isOpen) => {
  if (isOpen && props.template) {
    newlyCreatedKey.value = null
    await loadKeys()
  }
})

async function loadKeys() {
  if (!props.template) return

  isLoading.value = true
  try {
    const templateId = props.template.templateId || props.template.id
    const response = await templatesAPI.listInviteKeys(templateId)
    // Map Firebase fields to expected format
    keys.value = (response.keys || []).map(k => ({
      keyId: k.id,
      keyCode: k.key,
      usageLimit: k.usageLimit || k.maxUses,
      usageCount: k.usageCount || k.currentUses || 0,
      revoked: !k.isActive,
      createdAt: k.createdAt,
      expiresAt: k.expiresAt
    }))
  } catch (err) {
    keys.value = []
  } finally {
    isLoading.value = false
  }
}

async function createKey() {
  if (!props.template || isCreating.value) return

  isCreating.value = true
  try {
    const templateId = props.template.templateId || props.template.id

    const response = await templatesAPI.createInviteKey(templateId, {
      maxUses: newKey.usageLimit || 999,
      expiresInDays: newKey.expiresIn
    })

    if (!response.ok) {
      throw new Error(response.error || t('inviteKeys.errors.createFailed'))
    }

    newlyCreatedKey.value = response.key.key

    // Reload keys list
    await loadKeys()
  } catch (err) {
    showError(err.message || t('inviteKeys.errors.createFailed'))
  } finally {
    isCreating.value = false
  }
}

function confirmRevoke(key) {
  revokeConfirm.key = key
  revokeConfirm.show = true
}

async function revokeKey() {
  if (!revokeConfirm.key || isRevoking.value) return

  isRevoking.value = true
  try {
    const templateId = props.template.templateId || props.template.id
    const response = await templatesAPI.revokeInviteKey(templateId, revokeConfirm.key.keyId)

    if (!response.ok) {
      throw new Error(response.error || t('inviteKeys.errors.revokeFailed'))
    }

    // Update local state
    const key = keys.value.find(k => k.keyId === revokeConfirm.key.keyId)
    if (key) {
      key.revoked = true
    }

    revokeConfirm.show = false
    revokeConfirm.key = null
  } catch (err) {
    showError(err.message || t('inviteKeys.errors.revokeFailed'))
  } finally {
    isRevoking.value = false
  }
}

async function copyKey(keyCode) {
  try {
    await navigator.clipboard.writeText(keyCode)
    showSuccess(t('common.copied'))
  } catch (err) {
    showError(t('inviteKeys.copyHint'))
  }
}

function maskKey(keyCode) {
  if (!keyCode) return ''
  // Show first and last parts, mask middle
  const parts = keyCode.split('-')
  if (parts.length >= 4) {
    return `${parts[0]}-****-****-${parts[parts.length - 1]}`
  }
  return keyCode.slice(0, 8) + '****' + keyCode.slice(-4)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const diff = date - Date.now()

  // Future date (expires) — use locale-aware formatting
  if (diff > 0) {
    const days = Math.ceil(diff / MS_PER_DAY)
    if (days <= 30) return t('inviteKeys.days', { count: days })
    return date.toLocaleDateString(locale.value)
  }

  // Past date (created) — use i18n relative time
  return formatRelativeTime(dateStr)
}

function close() {
  emit('update:modelValue', false)
}
</script>
