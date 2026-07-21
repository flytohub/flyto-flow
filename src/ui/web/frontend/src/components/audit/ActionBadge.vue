<template>
  <span
    class="px-2 py-0.5 text-xs font-medium rounded-full"
    :class="badgeClasses"
  >
    {{ displayAction }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  action: {
    type: String,
    required: true
  }
})

const { t } = useI18n()

const actionConfig = computed(() => ({
  create: { label: t('actionLabel.create'), color: 'green' },
  read: { label: t('audit.actions.read'), color: 'blue' },
  update: { label: t('actionLabel.update'), color: 'yellow' },
  delete: { label: t('actionLabel.delete'), color: 'red' },
  login: { label: t('auth.login'), color: 'purple' },
  logout: { label: t('actionLabel.logout'), color: 'gray' },
  execute: { label: t('actionLabel.execute'), color: 'cyan' },
  export: { label: t('actionLabel.export'), color: 'indigo' },
  import: { label: t('actionLabel.import'), color: 'indigo' }
}))

const badgeClasses = computed(() => {
  const config = actionConfig.value[props.action] || { color: 'gray' }
  const colorMap = {
    green: 'bg-green-500/20 text-green-400',
    blue: 'bg-blue-500/20 text-blue-400',
    yellow: 'bg-yellow-500/20 text-yellow-400',
    red: 'bg-red-500/20 text-red-400',
    purple: 'bg-purple-500/20 text-purple-400',
    gray: 'bg-gray-500/20 text-gray-400',
    cyan: 'bg-cyan-500/20 text-cyan-400',
    indigo: 'bg-indigo-500/20 text-indigo-400'
  }
  return colorMap[config.color] || colorMap.gray
})

const displayAction = computed(() => {
  const config = actionConfig.value[props.action]
  if (config) {
    return config.label
  }
  return props.action
})
</script>
