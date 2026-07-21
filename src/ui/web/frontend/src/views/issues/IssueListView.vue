<template>
  <div>
    <!-- Filters -->
    <IssueFiltersBar
      :filter-status="filterStatus"
      :filter-type="filterType"
      :sort-by="sortBy"
      :type-dropdown-open="typeDropdownOpen"
      :sort-dropdown-open="sortDropdownOpen"
      :status-tabs="statusTabs"
      :type-options="typeOptions"
      :sort-options="sortOptions"
      @update:filter-status="$emit('update:filterStatus', $event)"
      @update:filter-type="$emit('update:filterType', $event)"
      @update:sort-by="$emit('update:sortBy', $event)"
      @toggle-type-dropdown="$emit('toggle-type-dropdown')"
      @toggle-sort-dropdown="$emit('toggle-sort-dropdown')"
      @close-type-dropdown="$emit('close-type-dropdown')"
      @close-sort-dropdown="$emit('close-sort-dropdown')"
    />

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-16">
      <Loader2 :size="32" class="animate-spin text-purple-500" />
    </div>

    <!-- Issue List -->
    <div v-else-if="issues.length" class="space-y-3">
      <IssueCard
        v-for="issue in issues"
        :key="issue.id"
        :issue="issue"
        :format-date="formatDate"
        @click="$emit('open-detail', issue)"
      />
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-16">
      <div class="w-16 h-16 rounded-2xl bg-gray-800/50 border border-white/10 flex items-center justify-center mx-auto mb-4">
        <CircleDot :size="32" class="text-gray-600" />
      </div>
      <p class="text-gray-500">{{ $t('issues.noIssues', 'No issues found.') }}</p>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex justify-center gap-2 mt-8">
      <button
        @click="$emit('update:currentPage', currentPage - 1)"
        :disabled="currentPage <= 1"
        class="px-4 py-2 text-sm rounded-xl bg-gray-800/50 border border-white/10 text-gray-400 hover:border-purple-500/30 hover:text-white disabled:opacity-50 transition-all"
      >
        {{ $t('common.previous', 'Previous') }}
      </button>
      <span class="px-4 py-2 text-sm text-gray-500">
        {{ currentPage }} / {{ totalPages }}
      </span>
      <button
        @click="$emit('update:currentPage', currentPage + 1)"
        :disabled="currentPage >= totalPages"
        class="px-4 py-2 text-sm rounded-xl bg-gray-800/50 border border-white/10 text-gray-400 hover:border-purple-500/30 hover:text-white disabled:opacity-50 transition-all"
      >
        {{ $t('common.next', 'Next') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { CircleDot, Loader2 } from 'lucide-vue-next'
import IssueCard from './IssueCard.vue'
import IssueFiltersBar from './IssueFiltersBar.vue'

defineProps({
  issues: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  currentPage: { type: Number, default: 1 },
  totalPages: { type: Number, default: 1 },
  filterStatus: { default: 'open' },
  filterType: { default: null },
  sortBy: { type: String, default: 'newest' },
  typeDropdownOpen: { type: Boolean, default: false },
  sortDropdownOpen: { type: Boolean, default: false },
  statusTabs: { type: Array, required: true },
  typeOptions: { type: Array, required: true },
  sortOptions: { type: Array, required: true },
  formatDate: { type: Function, required: true },
})

defineEmits([
  'update:filterStatus',
  'update:filterType',
  'update:sortBy',
  'update:currentPage',
  'toggle-type-dropdown',
  'toggle-sort-dropdown',
  'close-type-dropdown',
  'close-sort-dropdown',
  'open-detail',
])
</script>
