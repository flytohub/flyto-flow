<template>
  <div class="password-strength" role="status" :aria-label="ariaLabel">
    <div class="strength-bars">
      <div
        v-for="i in 4"
        :key="i"
        class="strength-bar"
        :class="{ active: i <= strengthLevel }"
        :style="{ backgroundColor: i <= strengthLevel ? strengthColor : undefined }"
      />
    </div>
    <span class="strength-label" :style="{ color: strengthColor }">
      {{ strengthLabel }}
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  password: {
    type: String,
    default: ''
  },
  minLength: {
    type: Number,
    default: 8
  }
})

const { t } = useI18n()

const strengthLevel = computed(() => {
  if (!props.password) return 0

  let score = 0
  const pwd = props.password

  // Length check
  if (pwd.length >= props.minLength) score++
  if (pwd.length >= 12) score++

  // Character variety checks
  if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score++
  if (/\d/.test(pwd)) score++
  if (/[^a-zA-Z0-9]/.test(pwd)) score++

  // Cap at 4
  return Math.min(score, 4)
})

const strengthColor = computed(() => {
  const colors = {
    0: '#9ca3af',
    1: '#ef4444',
    2: '#f59e0b',
    3: '#3b82f6',
    4: '#22c55e'
  }
  return colors[strengthLevel.value]
})

const strengthLabel = computed(() => {
  if (!props.password) return ''
  const labels = {
    1: t('auth.passwordWeak'),
    2: t('auth.passwordFair'),
    3: t('auth.passwordGood'),
    4: t('auth.passwordStrong')
  }
  return labels[strengthLevel.value] || ''
})

const ariaLabel = computed(() => {
  if (!props.password) return t('auth.enterPassword')
  return `${t('auth.passwordStrength')}: ${strengthLabel.value}`
})
</script>

<style scoped>
.password-strength {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.strength-bars {
  display: flex;
  gap: 4px;
  flex: 1;
}

.strength-bar {
  height: 4px;
  flex: 1;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.1);
  transition: background-color 0.3s ease;
}

.strength-label {
  font-size: 0.75rem;
  font-weight: 500;
  min-width: 60px;
  text-align: right;
}
</style>
