<template>
  <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 mb-6" role="toolbar" :aria-label="$t('templateToolbar.viewMode')">
    <!-- Search -->
    <div class="relative flex-1 max-w-md">
      <Search :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" aria-hidden="true" />
      <AppInput
        :modelValue="searchQuery"
        @update:modelValue="$emit('update:searchQuery', $event)"
        :placeholder="$t('templateToolbar.searchPlaceholder')"
        :aria-label="$t('templateToolbar.searchLabel')"
        class="!pl-9"
      />
    </div>

    <div class="flex items-center gap-3">
      <!-- Enter Selection Mode -->
      <button
        v-if="showSelectButton && !selectionMode"
        @click="$emit('enter-selection-mode')"
        class="flex items-center gap-2 px-3 py-2.5 min-h-[44px] text-sm font-medium rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
      >
        <CheckSquare :size="16" />
        {{ $t('batch.select', 'Select') }}
      </button>
      <!-- Select All (visible in selection mode) -->
      <button
        v-if="selectionMode"
        @click="$emit('select-all')"
        class="flex items-center gap-2 px-3 py-2.5 min-h-[44px] text-sm font-medium rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400"
      >
        <CheckSquare :size="16" />
        {{ $t('batch.selectAll') }}
      </button>

      <!-- Sort Dropdown -->
      <div class="relative" ref="sortRef">
        <button
          @click="sortOpen = !sortOpen"
          class="flex items-center gap-2 px-4 py-2.5 min-h-[44px] bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
          :aria-expanded="sortOpen"
          :aria-label="$t('templateToolbar.sortLabel')"
          aria-haspopup="listbox"
        >
          <ArrowUpDown :size="14" class="text-gray-400" />
          <span>{{ sortOptions.find(o => o.value === sortBy)?.label }}</span>
          <ChevronDown :size="14" class="text-gray-400 transition-transform" :class="{ 'rotate-180': sortOpen }" />
        </button>

        <Transition name="dropdown">
          <div v-if="sortOpen" class="absolute right-0 top-full mt-1.5 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg dark:shadow-black/30 z-50 py-1 overflow-hidden" role="listbox">
            <button
              v-for="opt in sortOptions"
              :key="opt.value"
              @click="selectSort(opt.value)"
              class="flex items-center justify-between w-full px-3 py-2 text-sm text-left transition-colors"
              :class="sortBy === opt.value
                ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'"
              role="option"
              :aria-selected="sortBy === opt.value"
            >
              {{ opt.label }}
              <Check v-if="sortBy === opt.value" :size="14" class="text-purple-500" />
            </button>
          </div>
        </Transition>
      </div>

      <!-- View toggle -->
      <div class="flex gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg" role="group" :aria-label="$t('templateToolbar.viewMode')">
        <button
          @click="$emit('update:viewMode', 'grid')"
          :class="viewMode === 'grid' ? 'bg-white dark:bg-gray-700 shadow-sm' : ''"
          class="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center rounded-md transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
          :aria-pressed="viewMode === 'grid'"
          :aria-label="$t('templateToolbar.gridView')"
        >
          <LayoutGrid :size="18" aria-hidden="true" />
        </button>
        <button
          @click="$emit('update:viewMode', 'list')"
          :class="viewMode === 'list' ? 'bg-white dark:bg-gray-700 shadow-sm' : ''"
          class="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center rounded-md transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
          :aria-pressed="viewMode === 'list'"
          :aria-label="$t('templateToolbar.listView')"
        >
          <List :size="18" aria-hidden="true" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Search, LayoutGrid, List, CheckSquare, ChevronDown, ArrowUpDown, Check } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'

const { t } = useI18n()

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  },
  sortBy: {
    type: String,
    default: 'updated'
  },
  viewMode: {
    type: String,
    default: 'grid'
  },
  showSelectButton: {
    type: Boolean,
    default: true
  },
  selectionMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:searchQuery', 'update:sortBy', 'update:viewMode', 'enter-selection-mode', 'select-all'])

const sortOpen = ref(false)
const sortRef = ref(null)

const sortOptions = computed(() => [
  { value: 'updated', label: t('templateToolbar.sortOptions.updated') },
  { value: 'created', label: t('templateToolbar.sortOptions.created') },
  { value: 'name', label: t('templateToolbar.sortOptions.name') },
  { value: 'status', label: t('templateToolbar.sortOptions.status') },
])

function selectSort(value) {
  emit('update:sortBy', value)
  sortOpen.value = false
}

function handleClickOutside(e) {
  if (sortRef.value && !sortRef.value.contains(e.target)) {
    sortOpen.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', handleClickOutside))
</script>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease-out;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
