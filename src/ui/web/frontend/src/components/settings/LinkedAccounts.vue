<template>
  <div class="bg-gray-800/40 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
    <div class="flex items-center gap-3 mb-6">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
        <Link2 :size="20" class="text-white" />
      </div>
      <div>
        <h2 class="text-lg font-semibold text-white">{{ $t('linkedAccounts.title') }}</h2>
        <p class="text-sm text-gray-400">{{ $t('linkedAccounts.subtitle') }}</p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-8">
      <Loader2 :size="24" class="animate-spin text-purple-400" />
    </div>

    <!-- Google Provider Row -->
    <div v-else class="space-y-4">
      <div class="flex items-center justify-between py-4 border-b border-white/5">
        <div class="flex items-center gap-3">
          <!-- Google icon -->
          <div class="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
          </div>
          <div>
            <div class="text-white font-medium">{{ $t('linkedAccounts.google') }}</div>
            <div v-if="isGoogleLinked" class="text-sm text-emerald-400 flex items-center gap-1">
              <CheckCircle :size="14" />
              {{ $t('linkedAccounts.linked') }}
            </div>
            <div v-else class="text-sm text-gray-500">
              {{ $t('linkedAccounts.notLinked') }}
            </div>
          </div>
        </div>

        <div>
          <button
            v-if="isGoogleLinked"
            @click="handleUnlink"
            :disabled="unlinking || !canUnlinkGoogle"
            class="px-4 py-2 text-sm text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            :title="!canUnlinkGoogle ? $t('linkedAccounts.cannotUnlink') : ''"
          >
            <Loader2 v-if="unlinking" :size="14" class="animate-spin" />
            {{ $t('linkedAccounts.unlink') }}
          </button>
          <button
            v-else-if="googleAuthEnabled"
            @click="handleLinkClick"
            :disabled="linking"
            class="px-4 py-2 text-sm text-purple-400 border border-purple-500/30 rounded-lg hover:bg-purple-500/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Loader2 v-if="linking" :size="14" class="animate-spin" />
            {{ $t('linkedAccounts.link') }}
          </button>
        </div>
      </div>

      <!-- Cannot unlink hint -->
      <p v-if="isGoogleLinked && !canUnlinkGoogle" class="text-xs text-amber-400/80">
        {{ $t('linkedAccounts.cannotUnlink') }}
      </p>
    </div>

    <!-- Messages -->
    <div v-if="errorMsg" class="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
      {{ errorMsg }}
    </div>
    <div v-if="successMsg" class="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400 text-sm">
      {{ successMsg }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Link2, CheckCircle, Loader2 } from 'lucide-vue-next'
import { authAPI } from '@/api/auth'
import { setGoogleClientId, isGoogleAuthEnabled, requestGoogleCredential } from '@/services/googleAuth'

const { t } = useI18n()

const loading = ref(true)
const linking = ref(false)
const unlinking = ref(false)
const providers = ref([])
const errorMsg = ref('')
const successMsg = ref('')

const googleAuthEnabled = ref(isGoogleAuthEnabled())
const isGoogleLinked = computed(() => providers.value.includes('google.com'))
const hasPassword = computed(() => providers.value.includes('password'))
const canUnlinkGoogle = computed(() => hasPassword.value)

onMounted(async () => {
  // Fetch auth config to get runtime Google client ID
  try {
    const config = await authAPI.getAuthConfig()
    if (config.google?.clientId) setGoogleClientId(config.google.clientId)
    googleAuthEnabled.value = config.google?.enabled && isGoogleAuthEnabled()
  } catch {
    // Keep compile-time default
  }
  await loadProviders()
})

async function loadProviders() {
  loading.value = true
  errorMsg.value = ''
  try {
    providers.value = await authAPI.getLinkedProviders()
  } catch (err) {
    errorMsg.value = err.userMessage || err.message
  } finally {
    loading.value = false
  }
}

async function handleLinkClick() {
  errorMsg.value = ''
  successMsg.value = ''
  linking.value = true
  try {
    const credential = await requestGoogleCredential()
    providers.value = await authAPI.linkGoogle(credential)
    successMsg.value = t('linkedAccounts.linkSuccess')
  } catch (err) {
    if (err) errorMsg.value = err.userMessage || err.message
  } finally {
    linking.value = false
  }
}

async function handleUnlink() {
  if (!canUnlinkGoogle.value) return

  errorMsg.value = ''
  successMsg.value = ''
  unlinking.value = true
  try {
    providers.value = await authAPI.unlinkProvider('google.com')
    successMsg.value = t('linkedAccounts.unlinkSuccess')
  } catch (err) {
    errorMsg.value = err.userMessage || err.message
  } finally {
    unlinking.value = false
  }
}
</script>
