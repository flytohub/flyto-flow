<template>
  <div class="flex flex-wrap gap-3">
    <!-- Search -->
    <div class="flex-1 min-w-[200px]">
      <div class="relative">
        <Search :size="18" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <AppInput
          :modelValue="filters.search"
          @update:modelValue="handleSearchInput"
          :placeholder="$t('audit.filter.searchPlaceholder', 'Search logs...')"
          class="!pl-10"
        />
      </div>
    </div>

    <!-- Action Filter -->
    <AppSelect
      :modelValue="filters.action || ''"
      @update:modelValue="updateFilter('action', $event || null)"
      :options="[
        { value: '', label: $t('audit.filter.allActions', 'All Actions') },
        { value: 'create', label: $t('audit.action.create', 'Create') },
        { value: 'read', label: $t('audit.action.read', 'Read') },
        { value: 'update', label: $t('audit.action.update', 'Update') },
        { value: 'delete', label: $t('audit.action.delete', 'Delete') },
        { value: 'login', label: $t('audit.action.login', 'Login') },
        { value: 'logout', label: $t('audit.action.logout', 'Logout') },
        { value: 'execute', label: $t('audit.action.execute', 'Execute') }
      ]"
    />

    <!-- Resource Type Filter -->
    <AppSelect
      :modelValue="filters.resource_type || ''"
      @update:modelValue="updateFilter('resource_type', $event || null)"
      :options="[
        { value: '', label: $t('audit.filter.allResources', 'All Resources') },
        { value: 'workflow', label: $t('audit.resource.workflow', 'Workflow') },
        { value: 'template', label: $t('audit.resource.template', 'Template') },
        { value: 'execution', label: $t('audit.resource.execution', 'Execution') },
        { value: 'user', label: $t('audit.resource.user', 'User') },
        { value: 'setting', label: $t('audit.resource.setting', 'Setting') }
      ]"
    />

    <!-- Date Range -->
    <div class="flex items-center gap-2">
      <input
        :value="filters.start_date"
        @change="updateFilter('start_date', $event.target.value || null)"
        type="date"
        class="px-3 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
      />
      <span class="text-gray-400">-</span>
      <input
        :value="filters.end_date"
        @change="updateFilter('end_date', $event.target.value || null)"
        type="date"
        class="px-3 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
      />
    </div>

    <!-- Clear Filters -->
    <button
      v-if="hasActiveFilters"
      @click="clearFilters"
      class="px-3 py-2.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
    >
      <X :size="16" />
      {{ $t('common.clearFilters', 'Clear') }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Search, X } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'

const props = defineProps({
  filters: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:filters'])

const hasActiveFilters = computed(() => {
  return Object.values(props.filters).some(v => v !== null && v !== '')
})

function updateFilter(key, value) {
  emit('update:filters', { ...props.filters, [key]: value })
}

let searchTimeout = null
function handleSearchInput(value) {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    updateFilter('search', value)
  }, 300)
}

function clearFilters() {
  emit('update:filters', {
    userId: null,
    action: null,
    resourceType: null,
    startDate: null,
    endDate: null,
    search: ''
  })
}
</script>
