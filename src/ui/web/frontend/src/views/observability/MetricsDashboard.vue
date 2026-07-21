<template>
  <div class="container mx-auto px-4 py-6">
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <!-- Total Executions -->
      <StatCard
        :title="$t('metrics.stats.totalExecutions', 'Total Executions')"
        :value="metricsStore.summary.totalExecutions"
        :change="metricsStore.summary.executionsChange"
        :loading="metricsStore.isLoading"
        icon="BarChart3"
        color="blue"
      />

      <!-- Success Rate -->
      <StatCard
        :title="$t('metrics.stats.successRate', 'Success Rate')"
        :value="formatPercent(metricsStore.summary.successRate)"
        :change="metricsStore.summary.successRateChange"
        :loading="metricsStore.isLoading"
        icon="CheckCircle"
        color="green"
        suffix="%"
      />

      <!-- Avg Duration -->
      <StatCard
        :title="$t('metrics.stats.avgDuration', 'Avg Duration')"
        :value="metricsStore.formattedAvgDuration"
        :change="metricsStore.summary.durationChange"
        :loading="metricsStore.isLoading"
        icon="Clock"
        color="purple"
        :inverse-change="true"
      />

      <!-- Failed Executions -->
      <StatCard
        :title="$t('metrics.stats.failed', 'Failed')"
        :value="metricsStore.summary.failed"
        :change="metricsStore.summary.failuresChange"
        :loading="metricsStore.isLoading"
        icon="XCircle"
        color="red"
        :inverse-change="true"
      />
    </div>

    <!-- Trend Chart -->
    <div class="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-white flex items-center gap-2">
          <TrendingUp :size="20" class="text-purple-400" />
          {{ $t('metrics.chart.title', 'Execution Trend') }}
        </h3>
      </div>

      <!-- Chart -->
      <div v-if="metricsStore.isLoading" class="h-64 flex items-center justify-center">
        <div class="animate-pulse flex items-center gap-2 text-gray-400">
          <Loader2 :size="20" class="animate-spin" />
          {{ $t('common.loading', 'Loading...') }}
        </div>
      </div>

      <div v-else-if="metricsStore.trend.length === 0" class="h-64 flex items-center justify-center">
        <div class="text-center text-gray-400">
          <BarChart3 :size="48" class="mx-auto mb-2 opacity-50" />
          <p>{{ $t('metrics.chart.noData', 'No data available') }}</p>
        </div>
      </div>

      <div v-else class="h-64">
        <canvas ref="chartCanvas"></canvas>
      </div>
    </div>

    <!-- Bottom Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Top Workflows -->
      <div class="bg-gray-800 rounded-xl border border-gray-700 p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white flex items-center gap-2">
            <Flame :size="20" class="text-orange-400" />
            {{ $t('metrics.topWorkflows.title', 'Top Workflows') }}
          </h3>
        </div>

        <div v-if="metricsStore.isLoading" class="space-y-3">
          <div v-for="i in 5" :key="i" class="h-12 bg-gray-700/50 rounded animate-pulse"></div>
        </div>

        <div v-else-if="metricsStore.topWorkflows.length === 0" class="py-8 text-center text-gray-400">
          <Workflow :size="48" class="mx-auto mb-2 opacity-50" />
          <p>{{ $t('metrics.topWorkflows.noData', 'No workflows executed yet') }}</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="(workflow, index) in metricsStore.topWorkflows"
            :key="workflow.id"
            class="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg hover:bg-gray-700/50 transition-colors"
          >
            <div class="flex items-center gap-3">
              <span class="w-6 h-6 rounded-full bg-gray-600 flex items-center justify-center text-sm font-medium text-gray-300">
                {{ index + 1 }}
              </span>
              <div>
                <p class="text-white font-medium truncate max-w-[200px]">{{ workflow.name }}</p>
                <p class="text-sm text-gray-400">{{ workflow.executions }} {{ $t('metrics.topWorkflows.executions', 'executions') }}</p>
              </div>
            </div>
            <div class="text-right">
              <p class="text-sm font-medium" :class="getSuccessRateColor(workflow.successRate)">
                {{ formatPercent(workflow.successRate) }}%
              </p>
              <p class="text-xs text-gray-500">{{ formatDuration(workflow.avgDurationMs) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Failures -->
      <div class="bg-gray-800 rounded-xl border border-gray-700 p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white flex items-center gap-2">
            <AlertTriangle :size="20" class="text-red-400" />
            {{ $t('metrics.recentFailures.title', 'Recent Failures') }}
          </h3>
        </div>

        <div v-if="metricsStore.isLoading" class="space-y-3">
          <div v-for="i in 5" :key="i" class="h-12 bg-gray-700/50 rounded animate-pulse"></div>
        </div>

        <div v-else-if="metricsStore.recentFailures.length === 0" class="py-8 text-center text-gray-400">
          <CheckCircle :size="48" class="mx-auto mb-2 opacity-50 text-green-400" />
          <p>{{ $t('metrics.recentFailures.noData', 'No recent failures') }}</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="failure in metricsStore.recentFailures"
            :key="failure.executionId"
            class="p-3 bg-red-900/20 border border-red-900/30 rounded-lg"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3 overflow-hidden">
                <XCircle :size="18" class="text-red-400 flex-shrink-0" />
                <p class="text-white font-medium truncate">{{ failure.workflowName }}</p>
              </div>
              <div class="flex items-center gap-2 flex-shrink-0 ml-4">
                <button
                  @click="copyError(failure.executionId, failure.error)"
                  class="p-1 rounded text-gray-400 hover:text-white hover:bg-gray-700/50 transition-colors"
                  :title="$t('metrics.recentFailures.copy', 'Copy error')"
                >
                  <Check v-if="copiedId === failure.executionId" :size="14" class="text-green-400" />
                  <Copy v-else :size="14" />
                </button>
                <p class="text-sm text-gray-400">{{ formatRelativeTime(failure.failedAt) }}</p>
              </div>
            </div>
            <div
              class="mt-2 ml-[30px] text-sm text-red-400/70 cursor-pointer select-text"
              :class="expandedFailures[failure.executionId] ? '' : 'line-clamp-2'"
              @click="expandedFailures[failure.executionId] = !expandedFailures[failure.executionId]"
            >
              {{ failure.error }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { MS_PER_MINUTE, MS_PER_HOUR, MS_PER_DAY } from '@/constants/time'
import { useMetricsStore } from '@/stores/metricsStore'
import {
  BarChart3,
  CheckCircle,
  Clock,
  XCircle,
  TrendingUp,
  Flame,
  Workflow,
  AlertTriangle,
  Loader2,
  Copy,
  Check
} from 'lucide-vue-next'
let Chart = null
async function getChart() {
  if (!Chart) { Chart = (await import('chart.js/auto')).default }
  return Chart
}
import StatCard from '@/components/metrics/StatCard.vue'
import { formatDuration } from '@/utils/format'

const props = defineProps({
  timeRange: {
    type: String,
    default: '7d'
  }
})

const { t } = useI18n()
const metricsStore = useMetricsStore()

// Failure expand/copy state
const expandedFailures = reactive({})
const copiedId = ref(null)

async function copyError(executionId, error) {
  try {
    await navigator.clipboard.writeText(error)
    copiedId.value = executionId
    setTimeout(() => { copiedId.value = null }, 2000)
  } catch {
    const el = document.querySelector(`[data-error-id="${executionId}"]`)
    if (el) { const r = document.createRange(); r.selectNodeContents(el); window.getSelection()?.removeAllRanges(); window.getSelection()?.addRange(r) }
  }
}

// Chart
const chartCanvas = ref(null)
let chartInstance = null

// Format helpers
function formatPercent(value) {
  return Number(value || 0).toFixed(1)
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  const minutes = Math.floor(diff / MS_PER_MINUTE)
  if (minutes < 1) return t('time.justNow', 'Just now')
  if (diff < MS_PER_HOUR) return t('time.minutesAgo', '{n} min ago', { n: minutes })

  const hours = Math.floor(diff / MS_PER_HOUR)
  if (diff < MS_PER_DAY) return t('time.hoursAgo', '{n}h ago', { n: hours })

  const days = Math.floor(diff / MS_PER_DAY)
  return t('time.daysAgo', '{n}d ago', { n: days })
}

function getSuccessRateColor(rate) {
  if (rate >= 95) return 'text-green-400'
  if (rate >= 80) return 'text-yellow-400'
  return 'text-red-400'
}

// Create/update chart
async function updateChart() {
  await getChart()
  if (!chartCanvas.value || !metricsStore.trend.length) return

  const ctx = chartCanvas.value.getContext('2d')

  if (chartInstance) {
    chartInstance.destroy()
  }

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: metricsStore.trend.map(p => p.label),
      datasets: [
        {
          label: t('metrics.chart.successful', 'Successful'),
          data: metricsStore.trend.map(p => p.successful),
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          fill: true,
          tension: 0.3
        },
        {
          label: t('metrics.chart.failed', 'Failed'),
          data: metricsStore.trend.map(p => p.failed),
          borderColor: 'rgb(239, 68, 68)',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          fill: true,
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#9ca3af',
            usePointStyle: true,
            padding: 20
          }
        }
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(75, 85, 99, 0.3)'
          },
          ticks: {
            color: '#9ca3af'
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(75, 85, 99, 0.3)'
          },
          ticks: {
            color: '#9ca3af',
            precision: 0
          }
        }
      }
    }
  })
}

// Load data
async function loadData() {
  await metricsStore.fetchAll(props.timeRange)
  nextTick(() => updateChart())
}

// Watch time range changes
watch(() => props.timeRange, () => {
  loadData()
})

// Watch trend data changes
watch(() => metricsStore.trend, () => {
  nextTick(() => updateChart())
}, { deep: true })

onMounted(() => {
  loadData()
})
</script>
