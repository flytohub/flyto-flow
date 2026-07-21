<template>
  <form @submit.prevent="handleSubmit" class="flex flex-col gap-5" novalidate>
    <div class="flex flex-col">
      <AuthInput
        v-model="form.username"
        :label="t('login.usernameLabel')"
        type="text"
        :placeholder="t('login.usernamePlaceholder')"
        :icon="UserIcon"
        :error="touched.username && errors.username"
        required
        autocomplete="username"
        @blur="touched.username = true"
      />
      <span v-if="touched.username && errors.username" class="mt-1.5 text-xs text-red-400 flex items-center gap-1" role="alert">
        {{ errors.username }}
      </span>
    </div>

    <div class="flex flex-col">
      <AuthInput
        v-model="form.email"
        :label="t('login.emailLabel')"
        type="email"
        :placeholder="t('login.emailPlaceholder')"
        :icon="MailIcon"
        :error="touched.email && errors.email"
        required
        autocomplete="email"
        @blur="touched.email = true"
      />
      <span v-if="touched.email && errors.email" class="mt-1.5 text-xs text-red-400 flex items-center gap-1" role="alert">
        {{ errors.email }}
      </span>
    </div>

    <div class="flex flex-col">
      <AuthInput
        v-model="form.password"
        :label="t('login.passwordLabel')"
        type="password"
        :placeholder="t('login.passwordMinLength')"
        :icon="LockIcon"
        :error="touched.password && errors.password"
        required
        :minlength="PASSWORD_MIN_LENGTH"
        autocomplete="new-password"
        @blur="touched.password = true"
      />
      <span class="mt-1 text-xs text-gray-400">{{ t('validation.passwordHint') }}</span>
      <PasswordStrengthMeter v-if="form.password" v-bind="{ password: form.password }" />
      <span v-if="touched.password && errors.password" class="mt-1.5 text-xs text-red-400 flex items-center gap-1" role="alert">
        {{ errors.password }}
      </span>
    </div>

    <div class="flex flex-col">
      <AuthInput
        v-model="form.confirmPassword"
        :label="t('login.confirmPasswordLabel')"
        type="password"
        :placeholder="t('login.confirmPasswordPlaceholder')"
        :icon="LockIcon"
        :error="touched.confirmPassword && errors.confirmPassword"
        required
        :minlength="PASSWORD_MIN_LENGTH"
        autocomplete="new-password"
        @blur="touched.confirmPassword = true"
      />
      <span v-if="touched.confirmPassword && errors.confirmPassword" class="mt-1.5 text-xs text-red-400 flex items-center gap-1" role="alert">
        {{ errors.confirmPassword }}
      </span>
    </div>

    <AuthButton :loading="loading" :disabled="!isValid" :icon="UserPlusIcon">
      {{ loading ? t('login.registering') : t('login.registerButton') }}
    </AuthButton>

    <!-- Social Login -->
    <template v-if="googleEnabled || githubEnabled">
      <div class="flex items-center gap-3 my-1">
        <div class="flex-1 h-px bg-white/10"></div>
        <span class="text-xs text-white/40">{{ t('login.orContinueWith') }}</span>
        <div class="flex-1 h-px bg-white/10"></div>
      </div>
      <div class="flex gap-3">
        <button
          v-if="googleEnabled"
          type="button"
          :disabled="googleLoading || loading"
          @click="handleGoogleClick"
          class="flex-1 flex items-center justify-center gap-3 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white/90 text-sm font-medium transition-all hover:bg-white/10 hover:border-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" class="shrink-0">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          Google
        </button>
        <button
          v-if="githubEnabled"
          type="button"
          :disabled="githubLoading || loading"
          @click="handleGithubClick"
          class="flex-1 flex items-center justify-center gap-3 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white/90 text-sm font-medium transition-all hover:bg-white/10 hover:border-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" class="shrink-0">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
          </svg>
          GitHub
        </button>
      </div>
    </template>
  </form>
</template>

<script setup>
import { reactive, computed, ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { User as UserIcon, Mail as MailIcon, Lock as LockIcon, UserPlus as UserPlusIcon } from 'lucide-vue-next'
import AuthInput from './AuthInput.vue'
import AuthButton from './AuthButton.vue'
import PasswordStrengthMeter from '@/components/common/PasswordStrengthMeter.vue'
import { formValidators, PASSWORD_MIN_LENGTH } from '@/utils/formValidation'
import { authAPI } from '@/api/auth'
import { setGoogleClientId, isGoogleAuthEnabled, requestGoogleCredential } from '@/services/googleAuth'
import { setGithubClientId, isGithubAuthEnabled, requestGithubCredential } from '@/services/githubAuth'

const { t } = useI18n()

defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['submit', 'google-login', 'github-login', 'desktop-oauth'])

const googleEnabled = ref(isGoogleAuthEnabled())
const googleLoading = ref(false)
const githubEnabled = ref(isGithubAuthEnabled())
const githubLoading = ref(false)

onMounted(async () => {
  try {
    const config = await authAPI.getAuthConfig()
    if (config.google?.clientId) setGoogleClientId(config.google.clientId)
    if (config.github?.clientId) setGithubClientId(config.github.clientId)
    googleEnabled.value = config.google?.enabled && isGoogleAuthEnabled()
    githubEnabled.value = config.github?.enabled && isGithubAuthEnabled()
  } catch {
    // Keep compile-time defaults on failure
  }
})

const isDesktop = !!window.__TAURI_INTERNALS__

async function handleGoogleClick() {
  googleLoading.value = true
  try {
    if (isDesktop) {
      emit('desktop-oauth', 'google')
    } else {
      const credential = await requestGoogleCredential()
      emit('google-login', credential)
    }
  } catch (err) {
    // OAuth error handled silently — user sees UI state
  } finally {
    googleLoading.value = false
  }
}

async function handleGithubClick() {
  githubLoading.value = true
  try {
    if (isDesktop) {
      emit('desktop-oauth', 'github')
    } else {
      const code = await requestGithubCredential()
      emit('github-login', code)
    }
  } catch (err) {
    // OAuth error handled silently — user sees UI state
  } finally {
    githubLoading.value = false
  }
}

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const touched = reactive({
  username: false,
  email: false,
  password: false,
  confirmPassword: false
})

const errors = computed(() => ({
  username: validateUsername(form.username),
  email: validateEmail(form.email),
  password: validatePassword(form.password),
  confirmPassword: validateConfirmPassword(form.confirmPassword)
}))

const isValid = computed(() => {
  return form.username && form.email && form.password && form.confirmPassword &&
    !errors.value.username && !errors.value.email && !errors.value.password && !errors.value.confirmPassword
})

function validateUsername(value) {
  const minError = formValidators.minLength(value, 3, t)
  if (minError) return minError
  const maxError = formValidators.maxLength(value, 30, t)
  if (maxError) return maxError
  return formValidators.alphanumeric(value, t)
}

const validateEmail = (value) => formValidators.email(value, t)
const validatePassword = (value) => formValidators.password(value, {
  minLength: PASSWORD_MIN_LENGTH,
  requireUppercase: false,
  requireLowercase: false,
  requireNumber: false
}, t)
const validateConfirmPassword = (value) => formValidators.confirmPassword(value, form.password, t)

function handleSubmit() {
  touched.username = true
  touched.email = true
  touched.password = true
  touched.confirmPassword = true

  if (isValid.value) {
    const { confirmPassword, ...submitData } = form
    emit('submit', submitData)
  }
}

function getFormData() {
  return { ...form }
}

defineExpose({ getFormData })
</script>
