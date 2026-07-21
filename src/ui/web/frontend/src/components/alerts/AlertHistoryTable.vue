<template>
  <div class="overflow-x-auto">
    <table class="w-full">
      <thead>
        <tr class="text-left text-xs text-gray-400 uppercase tracking-wider border-b border-gray-700">
          <th class="px-4 py-3">{{ $t('alerts.history.rule', 'Rule') }}</th>
          <th class="px-4 py-3">{{ $t('alerts.history.workflow', 'Workflow') }}</th>
          <th class="px-4 py-3">{{ $t('alerts.history.severity', 'Severity') }}</th>
          <th class="px-4 py-3">{{ $t('alerts.history.triggered', 'Triggered') }}</th>
          <th class="px-4 py-3">{{ $t('alerts.history.resolved', 'Resolved') }}</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-700">
        <tr
          v-for="item in history"
          :key="item.id"
          class="hover:bg-gray-700/30 transition-colors"
        >
          <td class="px-4 py-4">
            <div>
              <p class="text-white font-medium">{{ item.ruleName }}</p>
              <p class="text-sm text-gray-400 truncate max-w-[200px]">{{ item.message }}</p>
            </div>
          </td>
          <td class="px-4 py-4">
            <span class="text-gray-300">{{ item.workflowName || '-' }}</span>
          </td>
          <td class="px-4 py-4">
            <SeverityBadge :severity="item.severity" />
          </td>
          <td class="px-4 py-4">
            <span class="text-sm text-gray-300">{{ formatDateTime(item.triggeredAt) }}</span>
          </td>
          <td class="px-4 py-4">
            <span v-if="item.resolvedAt" class="text-sm text-green-400">
              {{ formatDateTime(item.resolvedAt) }}
            </span>
            <span v-else class="text-sm text-gray-500">-</span>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Empty State -->
    <div v-if="history.length === 0" class="py-12 text-center text-gray-400">
      <History :size="48" class="mx-auto mb-3 opacity-50" />
      <p>{{ $t('alerts.history.empty', 'No alert history') }}</p>
    </div>

    <!-- Pagination -->
    <div v-if="pagination.totalPages > 1" class="px-4 py-3 border-t border-gray-700 flex items-center justify-between">
      <span class="text-sm text-gray-400">
        {{ $t('common.pagination.showing', 'Showing') }} {{ ((pagination.page - 1) * pagination.limit) + 1 }}-{{ Math.min(pagination.page * pagination.limit, pagination.total) }}
        {{ $t('common.pagination.of', 'of') }} {{ pagination.total }}
      </span>
      <div class="flex items-center gap-2">
        <button
          @click="$emit('page-change', pagination.page - 1)"
          :disabled="pagination.page <= 1"
          class="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeft :size="18" />
        </button>
        <span class="text-sm text-gray-400">
          {{ pagination.page }} / {{ pagination.totalPages }}
        </span>
        <button
          @click="$emit('page-change', pagination.page + 1)"
          :disabled="pagination.page >= pagination.totalPages"
          class="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronRight :size="18" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { History, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import SeverityBadge from './SeverityBadge.vue'

defineProps({
  history: {
    type: Array,
    required: true
  },
  pagination: {
    type: Object,
    default: () => ({ page: 1, limit: 20, total: 0, totalPages: 1 })
  }
})

defineEmits(['page-change'])

function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString()
}
</script>
