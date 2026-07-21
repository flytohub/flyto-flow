<template>
  <span
    class="px-2 py-0.5 text-xs font-medium rounded-full"
    :class="badgeClasses"
  >
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  severity: {
    type: String,
    default: 'info',
    validator: (v) => ['critical', 'warning', 'info'].includes(v)
  }
})

const { t } = useI18n()

const badgeClasses = computed(() => {
  switch (props.severity) {
    case 'critical':
      return 'bg-red-500/20 text-red-400'
    case 'warning':
      return 'bg-yellow-500/20 text-yellow-400'
    default:
      return 'bg-blue-500/20 text-blue-400'
  }
})

const label = computed(() => {
  switch (props.severity) {
    case 'critical':
      return t('alerts.severity.critical', 'Critical')
    case 'warning':
      return t('alerts.severity.warning', 'Warning')
    default:
      return t('alerts.severity.info', 'Info')
  }
})
</script>
