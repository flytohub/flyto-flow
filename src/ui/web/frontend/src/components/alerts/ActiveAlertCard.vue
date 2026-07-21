<template>
  <div
    class="p-4 rounded-lg border transition-colors"
    :class="severityClasses"
  >
    <div class="flex items-start gap-3">
      <!-- Severity Icon -->
      <div class="flex-shrink-0 mt-0.5">
        <AlertTriangle v-if="alert.severity === 'critical'" :size="20" class="text-red-400" />
        <AlertCircle v-else-if="alert.severity === 'warning'" :size="20" class="text-yellow-400" />
        <Info v-else :size="20" class="text-blue-400" />
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="font-medium text-white truncate">{{ alert.ruleName }}</span>
          <SeverityBadge :severity="alert.severity" />
        </div>

        <p class="text-sm text-gray-300 mb-2">{{ alert.message }}</p>

        <div class="flex items-center gap-4 text-xs text-gray-400">
          <span class="flex items-center gap-1">
            <Workflow :size="12" />
            {{ alert.workflowName || $t('alerts.allWorkflows') }}
          </span>
          <span class="flex items-center gap-1">
            <Clock :size="12" />
            {{ formatRelativeTime(alert.triggeredAt) }}
          </span>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex-shrink-0 flex items-center gap-2">
        <button
          v-if="!alert.acknowledged"
          @click="$emit('acknowledge', alert.id)"
          :disabled="loading"
          class="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
          :title="$t('alerts.actions.acknowledge', 'Acknowledge')"
        >
          <Check :size="16" />
        </button>
        <span v-else class="text-xs text-green-400 flex items-center gap-1">
          <CheckCircle :size="14" />
          {{ $t('alerts.status.acknowledged', 'Acknowledged') }}
        </span>

        <button
          @click="$emit('mute', alert.id)"
          :disabled="loading"
          class="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
          :title="$t('alerts.actions.mute', 'Mute')"
        >
          <BellOff :size="16" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  AlertTriangle,
  AlertCircle,
  Info,
  Workflow,
  Clock,
  Check,
  CheckCircle,
  BellOff
} from 'lucide-vue-next'
import SeverityBadge from './SeverityBadge.vue'

const props = defineProps({
  alert: {
    type: Object,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['acknowledge', 'mute'])

const { t } = useI18n()

const severityClasses = computed(() => {
  switch (props.alert.severity) {
    case 'critical':
      return 'bg-red-900/20 border-red-800/50'
    case 'warning':
      return 'bg-yellow-900/20 border-yellow-800/50'
    default:
      return 'bg-blue-900/20 border-blue-800/50'
  }
})

function formatRelativeTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return t('time.justNow', 'Just now')
  if (minutes < 60) return t('time.minutesAgo', '{n} min ago', { n: minutes })

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return t('time.hoursAgo', '{n}h ago', { n: hours })

  const days = Math.floor(hours / 24)
  return t('time.daysAgo', '{n}d ago', { n: days })
}
</script>
