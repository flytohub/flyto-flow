<template>
  <div class="min-h-screen flex flex-col items-center justify-center p-4 relative overflow-hidden bg-[#0a0a0f]">
    <AnimatedBackground :particle-count="20" />

    <div class="login-container flex w-full bg-white/3 backdrop-blur-[20px] rounded-3xl border border-white/10 overflow-hidden relative z-1 flex-col max-w-[420px] md:flex-row md:max-w-[1000px] md:min-h-[600px]">
      <LoginBranding
        :subtitle="$t('login.subtitle')"
        :features="brandingFeatures"
      />

      <div class="flex-1 flex items-center justify-center p-8 md:p-12">
        <div class="form-card w-full max-w-[380px]">
          <div class="text-center mb-8">
            <h2 class="text-[1.75rem] font-bold text-white mb-2">{{ mode === 'login' ? $t('login.welcomeBack') : $t('login.createAccount') }}</h2>
            <p class="text-white/70 text-[0.9rem]">{{ mode === 'login' ? $t('login.loginPrompt') : $t('login.registerPrompt') }}</p>
          </div>

          <TabSwitcher v-model="mode" :tabs="tabOptions" />

          <ErrorAlert :message="error" />

          <LoginForm
            v-if="mode === 'login'"
            ref="loginFormRef"
            :loading="loading"
            @submit="handleLogin"
            @google-login="handleGoogleLogin"
            @github-login="handleGithubLogin"
            @desktop-oauth="handleDesktopOAuth"
          />

          <RegisterForm
            v-else
            :loading="loading"
            @submit="handleRegister"
            @google-login="handleGoogleLogin"
            @github-login="handleGithubLogin"
            @desktop-oauth="handleDesktopOAuth"
          />
        </div>
      </div>
    </div>

    <ChangePasswordModal
      :visible="showChangePassword"
      :loading="loading"
      :error="passwordError"
      @submit="handleChangePassword"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { LogIn, UserPlus, Zap, Shield, Sparkles } from 'lucide-vue-next'
import { authAPI } from '../api/auth'
import { useUserStore } from '@/stores/userStore'
import AnimatedBackground from '@/components/login/AnimatedBackground.vue'
import LoginBranding from '@/components/login/LoginBranding.vue'
import TabSwitcher from '@/components/login/TabSwitcher.vue'
import ErrorAlert from '@/components/login/ErrorAlert.vue'
import LoginForm from '@/components/login/LoginForm.vue'
import RegisterForm from '@/components/login/RegisterForm.vue'
import ChangePasswordModal from '@/components/login/ChangePasswordModal.vue'

const router = useRouter()
const { t } = useI18n()
const userStore = useUserStore()

const mode = ref('login')
const loading = ref(false)
const error = ref('')
const showChangePassword = ref(false)
const passwordError = ref('')
const loginFormRef = ref(null)

const tabOptions = computed(() => [
  { value: 'login', label: t('login.loginTab'), icon: LogIn },
  { value: 'register', label: t('login.registerTab'), icon: UserPlus }
])

const brandingFeatures = computed(() => [
  { key: 'feature1', label: t('login.feature1'), icon: Zap },
  { key: 'feature2', label: t('login.feature2'), icon: Shield },
  { key: 'feature3', label: t('login.feature3'), icon: Sparkles }
])

watch(mode, () => {
  error.value = ''
})

function resolveAuthError(err, fallbackKey) {
  if (err.isNetworkError) return err.userMessage || t('errors.networkError')
  if (err.isTimeout) return err.userMessage || t('errors.timeout')

  const code = err.code || ''
  const codeMap = {
    'auth/user-not-found': 'login.invalidCredentials',
    'auth/wrong-password': 'login.invalidCredentials',
    'auth/invalid-credential': 'login.invalidCredentials',
    'auth/invalid-email': 'login.invalidEmail',
    'auth/too-many-requests': 'login.tooManyAttempts',
    'auth/email-already-in-use': 'login.emailInUse',
    'auth/weak-password': 'login.weakPassword'
  }

  if (codeMap[code]) return t(codeMap[code])
  return err.userMessage || err.message || t(fallbackKey)
}

/**
 * Pull the saved redirect-after-login pathname (stashed by client.js on
 * 401) and validate it's a safe same-origin path before honouring it.
 * Rejects anything that looks like an open-redirect payload:
 *   - absolute URLs ("http://evil.com/...")
 *   - protocol-relative ("//evil.com/...")
 *   - javascript: / data: / vbscript: URIs
 * Returns '/' as the safe default.
 */
function consumeRedirectAfterLogin() {
  try {
    const raw = sessionStorage.getItem('redirectAfterLogin')
    sessionStorage.removeItem('redirectAfterLogin')
    if (!raw || typeof raw !== 'string') return '/'
    if (!raw.startsWith('/') || raw.startsWith('//')) return '/'
    // Block obviously non-path shapes.
    if (/^\s*(javascript|data|vbscript):/i.test(raw)) return '/'
    // Don't loop back to /login.
    if (raw === '/login' || raw.startsWith('/login?')) return '/'
    return raw
  } catch {
    return '/'
  }
}

async function handleLogin(formData) {
  loading.value = true
  error.value = ''

  try {
    const data = await userStore.login(formData.email, formData.password)

    if (data?.mustChangePassword) {
      showChangePassword.value = true
    } else {
      router.push(consumeRedirectAfterLogin())
    }
  } catch (err) {
    error.value = resolveAuthError(err, 'login.loginFailed')
  } finally {
    loading.value = false
  }
}

async function handleRegister(formData) {
  loading.value = true
  error.value = ''

  try {
    await userStore.register(formData.username, formData.email, formData.password)
    router.push(consumeRedirectAfterLogin())
  } catch (err) {
    error.value = resolveAuthError(err, 'login.registerFailed')
  } finally {
    loading.value = false
  }
}

async function handleGoogleLogin(credential) {
  loading.value = true
  error.value = ''

  try {
    await userStore.googleLogin(credential)
    router.push(consumeRedirectAfterLogin())
  } catch (err) {
    error.value = resolveAuthError(err, 'login.loginFailed')
  } finally {
    loading.value = false
  }
}

async function handleGithubLogin(code) {
  loading.value = true
  error.value = ''

  try {
    await userStore.githubLogin(code)
    router.push(consumeRedirectAfterLogin())
  } catch (err) {
    error.value = resolveAuthError(err, 'login.loginFailed')
  } finally {
    loading.value = false
  }
}

async function handleDesktopOAuth(provider) {
  loading.value = true
  error.value = ''

  try {
    await userStore.desktopOAuth(provider)
    router.push(consumeRedirectAfterLogin())
  } catch (err) {
    error.value = resolveAuthError(err, 'login.loginFailed')
  } finally {
    loading.value = false
  }
}

async function handleChangePassword(formData) {
  passwordError.value = ''
  loading.value = true

  try {
    const loginData = loginFormRef.value?.getFormData()
    await authAPI.changePassword(loginData?.password || '', formData.newPassword)
    showChangePassword.value = false
    router.push(consumeRedirectAfterLogin())
  } catch (err) {
    passwordError.value = err.userMessage || t('login.changePasswordFailed')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  box-shadow:
    0 0 0 1px rgba(255,255,255,0.05),
    0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.form-card {
  animation: formSlideIn 0.6s ease-out 0.3s both;
}

@keyframes formSlideIn {
  from { opacity: 0; transform: translateX(30px); }
  to { opacity: 1; transform: translateX(0); }
}

@media (max-width: 768px) {
  .form-card {
    animation-delay: 0.1s;
  }
}
</style>
