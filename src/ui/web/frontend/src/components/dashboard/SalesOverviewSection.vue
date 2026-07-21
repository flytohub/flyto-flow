<template>
  <section class="py-8 bg-gray-900">
    <div class="container px-4">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-bold text-white flex items-center gap-2">
          <TrendingUp :size="20" class="text-cyan-400" />
          {{ $t('dashboardPage.salesOverview.title') }}
        </h2>
        <span class="px-3 py-1 bg-cyan-500/20 text-cyan-400 text-xs font-medium rounded-full border border-cyan-500/30">
          {{ $t('dashboardPage.salesOverview.last7Days') }}
        </span>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Sales Trend Chart -->
        <div class="lg:col-span-2 bg-gray-800/50 border border-gray-700/50 rounded-2xl p-6 backdrop-blur-sm">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-sm font-medium text-gray-400">{{ $t('dashboardPage.salesOverview.salesTrend') }}</h3>
            <div class="flex items-center gap-4">
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full bg-cyan-400"></div>
                <span class="text-xs text-gray-500">{{ $t('dashboardPage.stats.sales') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full bg-emerald-400"></div>
                <span class="text-xs text-gray-500">{{ $t('dashboardPage.stats.revenue') }}</span>
              </div>
            </div>
          </div>

          <!-- Chart Area -->
          <div v-if="salesTrend.length > 0" class="h-48">
            <canvas ref="chartCanvas"></canvas>
          </div>

          <!-- Empty State -->
          <div v-else class="h-48 flex flex-col items-center justify-center">
            <div class="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center mb-4 border border-gray-700">
              <BarChart3 :size="28" class="text-gray-600" />
            </div>
            <p class="text-gray-500 text-sm">{{ $t('dashboardPage.salesOverview.noSalesYet') }}</p>
            <p class="text-gray-600 text-xs mt-1">{{ $t('dashboardPage.salesOverview.publishToStart') }}</p>
          </div>
        </div>

        <!-- Stats Cards -->
        <div class="space-y-4">
          <!-- Skeleton loading state -->
          <template v-if="loading">
            <div v-for="i in 2" :key="i" class="bg-gray-800/50 border border-gray-700/50 rounded-xl p-5 backdrop-blur-sm">
              <div class="flex items-center gap-2 mb-3">
                <div class="w-8 h-8 rounded-lg bg-gray-700 animate-pulse"></div>
                <div class="h-3 w-20 bg-gray-700 rounded animate-pulse"></div>
              </div>
              <div class="h-9 w-24 bg-gray-600 rounded animate-pulse mb-2"></div>
              <div class="h-3 w-32 bg-gray-700 rounded animate-pulse"></div>
            </div>
          </template>
          <!-- Loaded state -->
          <template v-else>
            <!-- Total Sales Card -->
            <div class="bg-gray-800/50 border border-gray-700/50 rounded-xl p-5 backdrop-blur-sm relative overflow-hidden group">
              <div class="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div class="relative">
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                      <ShoppingBag :size="16" class="text-cyan-400" />
                    </div>
                    <span class="text-xs text-gray-500 uppercase tracking-wider">{{ $t('dashboardPage.salesOverview.totalSales') }}</span>
                  </div>
                  <TrendIndicator :value="trendStats.salesTrendPercent" />
                </div>
                <div class="text-3xl font-bold text-white font-mono">{{ stats.sales }}</div>
                <div class="text-xs text-gray-500 mt-1">{{ $t('dashboardPage.salesOverview.thisWeek') }}: {{ trendStats.totalSales }}</div>
              </div>
            </div>

            <!-- Total Revenue Card -->
            <div class="bg-gray-800/50 border border-gray-700/50 rounded-xl p-5 backdrop-blur-sm relative overflow-hidden group">
              <div class="absolute inset-0 bg-gradient-to-r from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div class="relative">
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                      <DollarSign :size="16" class="text-emerald-400" />
                    </div>
                    <span class="text-xs text-gray-500 uppercase tracking-wider">{{ $t('dashboardPage.salesOverview.totalRevenue') }}</span>
                  </div>
                  <TrendIndicator :value="trendStats.revenueTrendPercent" />
                </div>
                <div class="text-3xl font-bold text-white font-mono">{{ formatCurrency(stats.revenue) }}</div>
                <div class="text-xs text-gray-500 mt-1">{{ $t('dashboardPage.salesOverview.thisWeek') }}: {{ formatCurrency(trendStats.totalRevenue) }}</div>
              </div>
            </div>
          </template>

          <!-- Quick Action -->
          <button
            @click="$emit('publish')"
            class="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-medium rounded-xl p-4 transition-all hover:(from-purple-500 to-indigo-500 shadow-lg shadow-purple-500/25) flex items-center justify-center gap-2"
          >
            <Rocket :size="18" />
            {{ $t('publish.publishTemplate') }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, watch, onMounted, nextTick, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { TrendingUp, BarChart3, ShoppingBag, DollarSign, Rocket } from 'lucide-vue-next'
let Chart = null
async function getChart() {
  if (!Chart) { Chart = (await import('chart.js/auto')).default }
  return Chart
}
import TrendIndicator from '@/components/common/TrendIndicator.vue'
import { formatCurrency } from '@/utils/format'

const { t } = useI18n()

const props = defineProps({
  salesTrend: { type: Array, default: () => [] },
  trendStats: {
    type: Object,
    default: () => ({ totalSales: 0, totalRevenue: 0, salesTrendPercent: 0, revenueTrendPercent: 0 })
  },
  stats: { type: Object, default: () => ({ sales: 0, revenue: 0 }) },
  loading: { type: Boolean, default: false }
})

defineEmits(['publish'])

const chartCanvas = ref(null)
let chartInstance = null

async function initChart() {
  if (!chartCanvas.value || props.salesTrend.length === 0) return
  await getChart()

  const labels = props.salesTrend.map(d => d.day)
  const salesData = props.salesTrend.map(d => d.sales)
  const revenueData = props.salesTrend.map(d => d.revenue)

  const maxSales = Math.max(...salesData, 1)
  const maxRevenue = Math.max(...revenueData, 0.01)
  const salesSuggestedMax = Math.ceil(maxSales * 1.7)
  const revenueSuggestedMax = maxRevenue * 1.25

  if (chartInstance) {
    chartInstance.destroy()
  }

  chartInstance = new Chart(chartCanvas.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: t('dashboardPage.stats.sales'),
          data: salesData,
          borderColor: '#22d3ee',
          backgroundColor: '#22d3ee',
          borderWidth: 2,
          fill: false,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#22d3ee',
          yAxisID: 'y'
        },
        {
          label: t('dashboardPage.stats.revenue'),
          data: revenueData,
          borderColor: '#34d399',
          backgroundColor: '#34d399',
          borderWidth: 2,
          fill: false,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#34d399',
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: '#1f2937',
          borderColor: '#374151',
          borderWidth: 1,
          titleColor: '#9ca3af',
          bodyColor: '#fff',
          callbacks: {
            label: (ctx) => {
              if (ctx.dataset.yAxisID === 'y1') {
                return `${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`
              }
              return `${ctx.dataset.label}: ${ctx.raw}`
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#6b7280', font: { size: 10 } }
        },
        y: {
          type: 'linear',
          position: 'left',
          beginAtZero: true,
          suggestedMax: salesSuggestedMax,
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#22d3ee', stepSize: 1, font: { size: 10 } },
          title: { display: true, text: t('dashboardPage.stats.sales'), color: '#22d3ee', font: { size: 10 } }
        },
        y1: {
          type: 'linear',
          position: 'right',
          beginAtZero: true,
          suggestedMax: revenueSuggestedMax,
          grid: { display: false },
          ticks: { color: '#34d399', callback: (val) => formatCurrency(val), font: { size: 10 } },
          title: { display: true, text: t('dashboardPage.stats.revenue'), color: '#34d399', font: { size: 10 } }
        }
      },
      interaction: { mode: 'nearest', axis: 'x', intersect: false }
    }
  })
}

watch(() => props.salesTrend, async () => {
  await nextTick()
  initChart()
}, { deep: true })

onMounted(() => {
  if (props.salesTrend.length > 0) {
    initChart()
  }
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>
