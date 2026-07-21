<template>
  <div class="overflow-x-auto">
    <table class="w-full">
      <thead>
        <tr class="text-left text-xs text-gray-400 uppercase tracking-wider border-b border-gray-700">
          <th class="px-4 py-3">{{ $t('alerts.rules.name', 'Name') }}</th>
          <th class="px-4 py-3">{{ $t('alerts.rules.condition', 'Condition') }}</th>
          <th class="px-4 py-3">{{ $t('alerts.rules.severity', 'Severity') }}</th>
          <th class="px-4 py-3">{{ $t('alerts.rules.status', 'Status') }}</th>
          <th class="px-4 py-3 text-right">{{ $t('common.actions', 'Actions') }}</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-700">
        <tr
          v-for="rule in rules"
          :key="rule.id"
          class="hover:bg-gray-700/30 transition-colors"
        >
          <td class="px-4 py-4">
            <div>
              <p class="text-white font-medium">{{ rule.name }}</p>
              <p v-if="rule.description" class="text-sm text-gray-400 truncate max-w-[200px]">
                {{ rule.description }}
              </p>
            </div>
          </td>
          <td class="px-4 py-4">
            <div class="text-sm text-gray-300">
              <span class="font-mono bg-gray-700 px-2 py-0.5 rounded">
                {{ formatCondition(rule.condition) }}
              </span>
            </div>
          </td>
          <td class="px-4 py-4">
            <SeverityBadge :severity="rule.severity" />
          </td>
          <td class="px-4 py-4">
            <button
              @click="$emit('toggle', rule.id)"
              :disabled="loading"
              class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
              :class="rule.enabled ? 'bg-purple-600' : 'bg-gray-600'"
            >
              <span
                class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                :class="rule.enabled ? 'translate-x-6' : 'translate-x-1'"
              />
            </button>
          </td>
          <td class="px-4 py-4">
            <div class="flex items-center justify-end gap-2">
              <button
                @click="$emit('edit', rule)"
                :disabled="loading"
                class="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                :title="$t('common.edit', 'Edit')"
              >
                <Pencil :size="16" />
              </button>
              <button
                @click="$emit('delete', rule.id)"
                :disabled="loading"
                class="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-lg transition-colors"
                :title="$t('common.delete', 'Delete')"
              >
                <Trash2 :size="16" />
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Empty State -->
    <div v-if="rules.length === 0" class="py-12 text-center text-gray-400">
      <Bell :size="48" class="mx-auto mb-3 opacity-50" />
      <p>{{ $t('alerts.rules.empty', 'No alert rules configured') }}</p>
      <button
        @click="$emit('create')"
        class="mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
      >
        {{ $t('alerts.rules.createFirst', 'Create your first rule') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { Pencil, Trash2, Bell } from 'lucide-vue-next'
import SeverityBadge from './SeverityBadge.vue'

defineProps({
  rules: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['edit', 'delete', 'toggle', 'create'])

const { t } = useI18n()

function formatCondition(condition) {
  if (!condition) return '-'

  const typeLabels = {
    failure_rate: t('alerts.condition.failureRate', 'Failure Rate'),
    execution_count: t('alerts.condition.executionCount', 'Executions'),
    duration: t('alerts.condition.duration', 'Duration'),
    consecutive_failures: t('alerts.condition.consecutiveFailures', 'Consecutive Failures')
  }

  const operatorLabels = {
    gt: '>',
    gte: '>=',
    lt: '<',
    lte: '<=',
    eq: '='
  }

  const type = typeLabels[condition.type] || condition.type
  const operator = operatorLabels[condition.operator] || condition.operator
  const threshold = condition.threshold

  return `${type} ${operator} ${threshold}`
}
</script>
