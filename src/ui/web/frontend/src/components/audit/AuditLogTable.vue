<template>
  <div>
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="text-left text-xs text-gray-400 uppercase tracking-wider border-b border-gray-700">
            <th class="px-4 py-3">#</th>
            <th class="px-4 py-3">{{ $t('audit.table.timestamp', 'Timestamp') }}</th>
            <th class="px-4 py-3">{{ $t('audit.table.actor', 'Actor') }}</th>
            <th class="px-4 py-3">{{ $t('audit.table.action', 'Action') }}</th>
            <th class="px-4 py-3">{{ $t('audit.table.resource', 'Resource') }}</th>
            <th class="px-4 py-3 text-right">{{ $t('common.actions', 'Actions') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-700">
          <tr
            v-for="log in logs"
            :key="log.id"
            class="hover:bg-gray-700/30 transition-colors"
          >
            <td class="px-4 py-4">
              <span class="text-xs text-gray-500 font-mono">{{ log.sequenceNumber }}</span>
            </td>
            <td class="px-4 py-4">
              <span class="text-sm text-gray-300">{{ formatDateTime(log.timestamp) }}</span>
            </td>
            <td class="px-4 py-4">
              <div>
                <p class="text-white text-sm font-medium font-mono">{{ truncateId(log.userId) }}</p>
                <p class="text-xs text-gray-400">{{ log.userType }}</p>
              </div>
            </td>
            <td class="px-4 py-4">
              <ActionBadge :action="log.action" />
            </td>
            <td class="px-4 py-4">
              <div>
                <p class="text-sm text-white font-mono">{{ truncateId(log.resourceId) }}</p>
                <p class="text-xs text-gray-400">{{ log.resourceType }}</p>
              </div>
            </td>
            <td class="px-4 py-4 text-right">
              <button
                @click="$emit('view-details', log)"
                class="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                :title="$t('common.viewDetails', 'View Details')"
              >
                <Eye :size="16" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty State -->
    <div v-if="logs.length === 0 && !loading" class="py-12 text-center text-gray-400">
      <FileText :size="48" class="mx-auto mb-3 opacity-50" />
      <p>{{ $t('audit.table.empty', 'No audit logs found') }}</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="py-8 text-center">
      <Loader2 :size="32" class="mx-auto text-purple-400 animate-spin" />
    </div>

    <!-- Pagination -->
    <div v-if="pagination.totalPages > 1" class="px-4 py-3 border-t border-gray-700 flex items-center justify-between">
      <span class="text-sm text-gray-400">
        {{ $t('common.pagination.showing', 'Showing') }}
        {{ ((pagination.page - 1) * pagination.limit) + 1 }}-{{ Math.min(pagination.page * pagination.limit, pagination.total) }}
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
import { Eye, FileText, Loader2, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import ActionBadge from './ActionBadge.vue'

defineProps({
  logs: {
    type: Array,
    required: true
  },
  pagination: {
    type: Object,
    default: () => ({ page: 1, limit: 50, total: 0, totalPages: 1 })
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['view-details', 'page-change'])

function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

function truncateId(id) {
  if (!id) return '-'
  if (id.length <= 12) return id
  return `${id.slice(0, 6)}...${id.slice(-4)}`
}
</script>
