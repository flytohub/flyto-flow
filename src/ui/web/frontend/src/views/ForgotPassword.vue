<template>
  <div class="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-[#0a0a0f]">
    <AnimatedBackground :particle-count="15" />

    <div class="forgot-container w-full max-w-[420px] bg-white/3 backdrop-blur-[20px] rounded-3xl border border-white/10 overflow-hidden relative z-1">
      <div class="flex items-center justify-center p-8 sm:p-12">
        <div class="form-card w-full">
          <div class="flex justify-center mb-6">
            <Mail class="w-12 h-12 text-purple-500" />
          </div>

          <div class="text-center mb-8">
            <h2 class="text-2xl font-bold text-white mb-2">{{ $t('auth.forgotPassword.title') }}</h2>
            <p class="text-white/50 text-[0.9rem] leading-normal">{{ $t('auth.forgotPassword.subtitle') }}</p>
          </div>

          <!-- Success State -->
          <div v-if="submitted" class="text-center">
            <div class="flex justify-center mb-4">
              <CheckCircle class="w-12 h-12 text-emerald-500" />
            </div>
            <p class="text-white text-base font-medium mb-2">{{ $t('auth.forgotPassword.emailSent') }}</p>
            <p class="text-white/50 text-sm mb-6">{{ $t('auth.forgotPassword.checkInbox') }}</p>
            <router-link to="/login" class="flex items-center justify-center gap-2 text-white/50 no-underline text-sm transition-colors hover:text-purple-500">
              <ArrowLeft :size="16" />
              {{ $t('auth.forgotPassword.backToLogin') }}
            </router-link>
          </div>

          <!-- Form State -->
          <form v-else @submit.prevent="handleSubmit" class="flex flex-col gap-6">
            <ErrorAlert :message="error" />

            <AuthInput
              v-model="email"
              :label="$t('auth.forgotPassword.emailLabel')"
              type="email"
              :placeholder="$t('auth.forgotPassword.emailPlaceholder')"
              :icon="Mail"
              autocomplete="email"
              required
              autofocus
            />

            <AuthButton :loading="loading" :icon="SendIcon">
              {{ $t('auth.forgotPassword.sendLink') }}
            </AuthButton>

            <router-link to="/login" class="flex items-center justify-center gap-2 text-white/50 no-underline text-sm transition-colors hover:text-purple-500">
              <ArrowLeft :size="16" />
              {{ $t('auth.forgotPassword.backToLogin') }}
            </router-link>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Mail, ArrowLeft, CheckCircle, Send as SendIcon } from 'lucide-vue-next'
import AnimatedBackground from '@/components/login/AnimatedBackground.vue'
import AuthInput from '@/components/login/AuthInput.vue'
import AuthButton from '@/components/login/AuthButton.vue'
import ErrorAlert from '@/components/login/ErrorAlert.vue'
import { post } from '@/api/client'
import { ENDPOINTS } from '@/config/api'
import { telemetry } from '@/services/telemetry'

const { t } = useI18n()

const email = ref('')
const loading = ref(false)
const error = ref('')
const submitted = ref(false)

async function handleSubmit() {
  if (!email.value) {
    error.value = t('auth.forgotPassword.emailRequired')
    return
  }

  loading.value = true
  error.value = ''

  try {
    await post(ENDPOINTS.AUTH.FORGOT_PASSWORD, { email: email.value })
    submitted.value = true
    telemetry.track('auth.password_reset_request', { success: true })
  } catch (err) {
    const status = err.response?.status
    if (status === 404) {
      error.value = t('auth.forgotPassword.emailNotFound')
    } else if (status === 429) {
      error.value = t('auth.forgotPassword.tooManyAttempts')
    } else {
      error.value = err.userMessage || t('auth.forgotPassword.sendFailed')
    }
    telemetry.track('auth.password_reset_request', { success: false })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.forgot-container {
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
