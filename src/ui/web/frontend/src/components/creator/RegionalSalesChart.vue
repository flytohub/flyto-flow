<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
        {{ $t('creator.regionalSales.title', 'Sales by Region') }}
      </h3>

      <div class="relative" ref="periodRef">
        <button
          @click="periodOpen = !periodOpen"
          class="flex items-center gap-2 px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-500 transition-colors"
          :aria-expanded="periodOpen"
          aria-haspopup="listbox"
        >
          <span>{{ periodOptions.find(o => o.value === period)?.label }}</span>
          <ChevronDown :size="14" class="text-gray-400 transition-transform" :class="{ 'rotate-180': periodOpen }" />
        </button>
        <Transition name="dropdown">
          <div v-if="periodOpen" class="absolute right-0 top-full mt-1.5 w-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg dark:shadow-black/30 z-50 py-1 overflow-hidden" role="listbox">
            <button
              v-for="opt in periodOptions"
              :key="opt.value"
              @click="period = opt.value; periodOpen = false; $emit('periodChange', period)"
              class="flex items-center justify-between w-full px-3 py-2 text-sm text-left transition-colors"
              :class="period === opt.value
                ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'"
              role="option"
              :aria-selected="period === opt.value"
            >
              {{ opt.label }}
              <Check v-if="period === opt.value" :size="14" class="text-purple-500" />
            </button>
          </div>
        </Transition>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-64">
      <Loader2 class="w-8 h-8 animate-spin text-blue-500" />
    </div>

    <div v-else-if="!data.length" class="flex flex-col items-center justify-center h-64 text-gray-500">
      <Globe class="w-12 h-12 mb-4 opacity-50" />
      <p>{{ $t('creator.regionalSales.noData', 'No sales data available') }}</p>
    </div>

    <div v-else class="space-y-4">
      <!-- Summary Stats -->
      <div class="grid grid-cols-2 gap-4 mb-6">
        <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ $t('creator.regionalSales.totalSales', 'Total Sales') }}</p>
          <p class="text-2xl font-bold text-gray-900 dark:text-gray-100">{{ totalSales }}</p>
        </div>
        <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ $t('creator.regionalSales.totalRevenue', 'Total Revenue') }}</p>
          <p class="text-2xl font-bold text-green-600 dark:text-green-400">{{ formatCurrency(totalRevenue) }}</p>
        </div>
      </div>

      <!-- Regional bars -->
      <div class="space-y-3">
        <div v-for="region in data" :key="region.region" class="space-y-1">
          <div class="flex items-center justify-between text-sm">
            <div class="flex items-center gap-2">
              <span class="font-medium text-gray-900 dark:text-gray-100">{{ region.region_name }}</span>
              <span class="text-gray-500">({{ region.region }})</span>
            </div>
            <div class="flex items-center gap-4 text-gray-600 dark:text-gray-400">
              <span>{{ region.sales }} {{ $t('creator.regionalSales.sales', 'sales') }}</span>
              <span class="font-medium text-green-600 dark:text-green-400">{{ formatCurrency(region.revenue) }}</span>
            </div>
          </div>
          <div class="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :style="{ width: `${region.percentage}%`, backgroundColor: getRegionColor(region.region) }"
            ></div>
          </div>
          <div class="text-xs text-gray-500 text-right">{{ region.percentage }}%</div>
        </div>
      </div>

      <!-- Map visualization (simplified) -->
      <div class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <div class="flex flex-wrap gap-2">
          <div
            v-for="region in data"
            :key="region.region"
            class="px-3 py-1.5 rounded-full text-sm font-medium"
            :style="{ backgroundColor: getRegionColor(region.region) + '20', color: getRegionColor(region.region) }"
          >
            {{ region.region }}: {{ region.percentage }}%
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Loader2, Globe, ChevronDown, Check } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { formatCurrency } from '@/utils/format'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  totalSales: {
    type: Number,
    default: 0
  },
  totalRevenue: {
    type: Number,
    default: 0
  },
  loading: {
    type: Boolean,
    default: false
  },
  initialPeriod: {
    type: String,
    default: '30d'
  }
})

const { t } = useI18n()
const emit = defineEmits(['periodChange'])

const period = ref(props.initialPeriod)
const periodOpen = ref(false)
const periodRef = ref(null)

const periodOptions = computed(() => [
  { value: '7d', label: t('creator.period.7d', 'Last 7 days') },
  { value: '30d', label: t('creator.period.30d', 'Last 30 days') },
  { value: '90d', label: t('creator.period.90d', 'Last 90 days') },
  { value: 'all', label: t('creator.period.all', 'All time') },
])

function handleClickOutside(e) {
  if (periodRef.value && !periodRef.value.contains(e.target)) {
    periodOpen.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', handleClickOutside))

const regionColors = {
  US: '#3B82F6',
  TW: '#10B981',
  JP: '#F59E0B',
  KR: '#8B5CF6',
  CN: '#EF4444',
  HK: '#EC4899',
  SG: '#06B6D4',
  GB: '#6366F1',
  DE: '#F97316',
  FR: '#14B8A6',
  AU: '#A855F7',
  CA: '#22C55E',
  Unknown: '#6B7280'
}

function getRegionColor(code) {
  return regionColors[code] || '#6B7280'
}

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
