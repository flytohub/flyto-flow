<template>
  <div class="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-[#0a0a0f]">
    <AnimatedBackground :particle-count="15" />

    <div class="reset-container w-full max-w-[420px] bg-white/3 backdrop-blur-[20px] rounded-3xl border border-white/10 overflow-hidden relative z-1">
      <div class="flex items-center justify-center p-8 sm:p-12">
        <div class="form-card w-full">

          <!-- Loading State -->
          <div v-if="verifying" class="flex flex-col items-center justify-center py-8" aria-live="polite">
            <Loader2 class="w-12 h-12 text-purple-500 animate-spin" aria-hidden="true" />
            <p class="mt-4 text-white/50">{{ $t('auth.resetPassword.verifying') }}</p>
          </div>

          <!-- Invalid Token State -->
          <div v-else-if="tokenInvalid" class="text-center" role="alert">
            <div class="flex justify-center mb-4">
              <XCircle class="w-12 h-12 text-red-500" aria-hidden="true" />
            </div>
            <h2 class="text-xl font-semibold text-white mb-2">{{ $t('auth.resetPassword.invalidToken') }}</h2>
            <p class="text-white/50 text-sm mb-6">{{ $t('auth.resetPassword.tokenExpired') }}</p>
            <router-link to="/forgot-password" class="inline-flex items-center justify-center px-6 py-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl text-white font-medium no-underline transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-purple-500/30">
              {{ $t('auth.resetPassword.requestNew') }}
            </router-link>
          </div>

          <!-- Success State -->
          <div v-else-if="resetSuccess" class="text-center" role="status">
            <div class="flex justify-center mb-4">
              <CheckCircle class="w-12 h-12 text-emerald-500" aria-hidden="true" />
            </div>
            <h2 class="text-xl font-semibold text-white mb-2">{{ $t('auth.resetPassword.success') }}</h2>
            <p class="text-white/50 text-sm mb-6">{{ $t('auth.resetPassword.successMessage') }}</p>
            <router-link to="/login" class="inline-flex items-center justify-center px-6 py-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl text-white font-medium no-underline transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-purple-500/30">
              {{ $t('auth.resetPassword.goToLogin') }}
            </router-link>
          </div>

          <!-- Reset Form -->
          <template v-else>
            <div class="flex justify-center mb-6">
              <KeyRound class="w-12 h-12 text-purple-500" />
            </div>

            <div class="text-center mb-8">
              <h2 class="text-2xl font-bold text-white mb-2">{{ $t('auth.resetPassword.title') }}</h2>
              <p class="text-white/50 text-[0.9rem] leading-normal">{{ $t('auth.resetPassword.subtitle') }}</p>
              <p v-if="tokenEmail" class="mt-2 text-purple-400 text-sm font-medium">{{ tokenEmail }}</p>
            </div>

            <form @submit.prevent="handleSubmit" class="flex flex-col gap-5">
              <ErrorAlert :message="error" />

              <AuthInput
                v-model="newPassword"
                :label="$t('auth.resetPassword.newPasswordLabel')"
                type="password"
                :placeholder="$t('auth.resetPassword.newPasswordPlaceholder')"
                :icon="Lock"
                autocomplete="new-password"
                required
                autofocus
              />

              <AuthInput
                v-model="confirmPassword"
                :label="$t('auth.resetPassword.confirmPasswordLabel')"
                type="password"
                :placeholder="$t('auth.resetPassword.confirmPasswordPlaceholder')"
                :icon="Lock"
                autocomplete="new-password"
                required
              />

              <!-- Password Requirements -->
              <div class="flex flex-col gap-2 p-3 bg-white/3 rounded-lg" aria-live="polite">
                <div class="flex items-center gap-2 text-xs transition-colors" :class="newPassword.length >= PASSWORD_MIN_LENGTH ? 'text-emerald-500' : 'text-white/40'">
                  <Check v-if="newPassword.length >= PASSWORD_MIN_LENGTH" :size="14" />
                  <X v-else :size="14" />
                  {{ $t('auth.resetPassword.minLength') }}
                </div>
                <div class="flex items-center gap-2 text-xs transition-colors" :class="hasLetterAndNumber ? 'text-emerald-500' : 'text-white/40'">
                  <Check v-if="hasLetterAndNumber" :size="14" />
                  <X v-else :size="14" />
                  {{ $t('auth.resetPassword.lettersAndNumbers') }}
                </div>
                <div class="flex items-center gap-2 text-xs transition-colors" :class="passwordsMatch && confirmPassword.length > 0 ? 'text-emerald-500' : 'text-white/40'">
                  <Check v-if="passwordsMatch && confirmPassword.length > 0" :size="14" />
                  <X v-else :size="14" />
                  {{ $t('auth.resetPassword.passwordsMatch') }}
                </div>
              </div>

              <AuthButton :loading="loading" :disabled="!canSubmit" :icon="KeyRound">
                {{ $t('auth.resetPassword.resetButton') }}
              </AuthButton>
            </form>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { KeyRound, Lock, CheckCircle, XCircle, Loader2, Check, X } from 'lucide-vue-next'
import AnimatedBackground from '@/components/login/AnimatedBackground.vue'
import AuthInput from '@/components/login/AuthInput.vue'
import AuthButton from '@/components/login/AuthButton.vue'
import ErrorAlert from '@/components/login/ErrorAlert.vue'
import { post } from '@/api/client'
import { ENDPOINTS } from '@/config/api'
import { PASSWORD_MIN_LENGTH } from '@/utils/formValidation'

const route = useRoute()
const { t } = useI18n()

const oobCode = ref('')
const tokenEmail = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const verifying = ref(true)
const tokenInvalid = ref(false)
const resetSuccess = ref(false)
const error = ref('')

const hasLetterAndNumber = computed(() => {
  return /[a-zA-Z]/.test(newPassword.value) && /[0-9]/.test(newPassword.value)
})

const passwordsMatch = computed(() => newPassword.value === confirmPassword.value)

const canSubmit = computed(() => {
  return (
    newPassword.value.length >= PASSWORD_MIN_LENGTH &&
    hasLetterAndNumber.value &&
    passwordsMatch.value
  )
})

onMounted(async () => {
  oobCode.value = route.query.oobCode || route.query.token || ''

  if (!oobCode.value) {
    tokenInvalid.value = true
    verifying.value = false
    return
  }

  try {
    const result = await post(ENDPOINTS.AUTH.VERIFY_RESET_CODE, {
      code: oobCode.value
    })
    if (result.ok && result.valid) {
      tokenEmail.value = result.email || ''
    } else {
      tokenInvalid.value = true
    }
  } catch {
    tokenInvalid.value = true
  } finally {
    verifying.value = false
  }
})

async function handleSubmit() {
  if (!canSubmit.value) return

  loading.value = true
  error.value = ''

  try {
    const result = await post(ENDPOINTS.AUTH.RESET_PASSWORD, {
      code: oobCode.value,
      new_password: newPassword.value
    })

    if (result.ok) {
      resetSuccess.value = true
    } else {
      error.value = result.error || t('auth.resetPassword.error')
    }
  } catch (err) {
    const detail = err.response?.data?.detail || err.userMessage || ''
    if (detail.includes('expired') || detail.includes('EXPIRED')) {
      error.value = t('auth.resetPassword.tokenExpired')
    } else if (detail.includes('weak') || detail.includes('WEAK')) {
      error.value = t('auth.resetPassword.weakPassword')
    } else {
      error.value = detail || t('auth.resetPassword.error')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.reset-container {
  box-shadow:
    0 0 0 1px rgba(255,255,255,0.05),
    0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.form-card {
  animation: formSlideIn 0.6s ease-out both;
}

@keyframes formSlideIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
