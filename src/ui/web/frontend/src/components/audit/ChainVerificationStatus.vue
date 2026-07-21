<template>
  <div
    class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg"
    :class="statusClasses"
  >
    <component :is="statusIcon" :size="16" :class="{ 'animate-spin': isVerifying }" />
    <span class="text-sm font-medium">{{ statusText }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ShieldCheck, ShieldAlert, Loader2, Shield } from 'lucide-vue-next'

const props = defineProps({
  verified: {
    type: Boolean,
    default: null
  },
  isVerifying: {
    type: Boolean,
    default: false
  },
  lastVerifiedAt: {
    type: String,
    default: null
  }
})

const { t } = useI18n()

const statusClasses = computed(() => {
  if (props.isVerifying) {
    return 'bg-blue-500/20 text-blue-400'
  }
  if (props.verified === true) {
    return 'bg-green-500/20 text-green-400'
  }
  if (props.verified === false) {
    return 'bg-red-500/20 text-red-400'
  }
  return 'bg-gray-500/20 text-gray-400'
})

const statusIcon = computed(() => {
  if (props.isVerifying) {
    return Loader2
  }
  if (props.verified === true) {
    return ShieldCheck
  }
  if (props.verified === false) {
    return ShieldAlert
  }
  return Shield
})

const statusText = computed(() => {
  if (props.isVerifying) {
    return t('audit.chain.verifying', 'Verifying...')
  }
  if (props.verified === true) {
    return t('audit.chain.verified', 'Chain Verified')
  }
  if (props.verified === false) {
    return t('audit.chain.broken', 'Chain Broken')
  }
  return t('audit.chain.unknown', 'Not Verified')
})
</script>
