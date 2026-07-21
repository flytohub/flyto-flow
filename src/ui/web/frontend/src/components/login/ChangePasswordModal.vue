<template>
  <Transition name="modal">
    <div v-if="visible" class="fixed inset-0 bg-black/70 backdrop-blur-[8px] flex items-center justify-center p-4 z-100" @click.self="() => {}">
      <div class="modal-card w-full max-w-[420px] bg-[rgba(30,30,40,0.95)] border border-white/10 rounded-[20px] p-8" role="dialog" aria-modal="true" aria-labelledby="change-password-title">
        <div class="flex items-start gap-4 mb-6">
          <div class="w-12 h-12 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl flex items-center justify-center text-white shrink-0" aria-hidden="true">
            <Key :size="24" />
          </div>
          <div>
            <h2 id="change-password-title" class="text-[1.25rem] font-bold text-white mb-1">{{ t('login.firstLoginTitle') }}</h2>
            <p class="text-[0.85rem] text-white/50">{{ t('login.firstLoginSubtitle') }}</p>
          </div>
        </div>

        <form @submit.prevent="handleSubmit" class="flex flex-col gap-5">
          <AuthInput
            v-model="form.newPassword"
            :label="t('login.newPasswordLabel')"
            type="password"
            :placeholder="t('login.newPasswordPlaceholder')"
            :icon="LockIcon"
            autocomplete="new-password"
            required
            minlength="6"
          />

          <AuthInput
            v-model="form.confirmPassword"
            :label="t('login.confirmPasswordLabel')"
            type="password"
            :placeholder="t('login.confirmPasswordPlaceholder')"
            :icon="LockIcon"
            autocomplete="new-password"
            required
            minlength="6"
          />

          <ErrorAlert :message="validationError || error" />

          <AuthButton :loading="loading" :icon="CheckIcon">
            {{ loading ? t('login.changing') : t('login.confirmChange') }}
          </AuthButton>
        </form>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Key, Lock as LockIcon, Check as CheckIcon } from 'lucide-vue-next'
import AuthInput from './AuthInput.vue'
import AuthButton from './AuthButton.vue'
import ErrorAlert from './ErrorAlert.vue'

const { t } = useI18n()

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['submit'])

const form = reactive({
  newPassword: '',
  confirmPassword: ''
})

const validationError = ref('')

watch(() => props.visible, (val) => {
  if (!val) {
    form.newPassword = ''
    form.confirmPassword = ''
    validationError.value = ''
  }
})

function handleSubmit() {
  validationError.value = ''

  if (form.newPassword.length < 6) {
    validationError.value = t('login.passwordMinError')
    return
  }

  if (form.newPassword !== form.confirmPassword) {
    validationError.value = t('login.passwordMismatch')
    return
  }

  emit('submit', { ...form })
}
</script>

<style scoped>
.modal-card {
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-card,
.modal-leave-to .modal-card {
  transform: scale(0.95) translateY(20px);
}
</style>
