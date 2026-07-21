<template>
  <div class="relative">
    <!-- Loading overlay -->
    <div
      v-if="isLoading"
      class="absolute inset-0 bg-gray-900/50 flex items-center justify-center rounded-lg z-10"
    >
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
    </div>

    <!-- Chart container -->
    <div ref="chartContainer" class="w-full" :style="{ height: `${height}px` }">
      <canvas ref="chartCanvas" />
    </div>

    <!-- Empty state -->
    <div
      v-if="!isLoading && (!chartData || chartData.length === 0)"
      class="absolute inset-0 flex items-center justify-center"
    >
      <div class="text-center text-gray-500">
        <BarChart3 :size="32" class="mx-auto mb-2 opacity-50" />
        <p class="text-sm">{{ $t('usage.chart.noData', 'No usage data yet') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { BarChart3 } from 'lucide-vue-next'
import { formatCompactNumber } from '@/utils/format'
import {
  Chart,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

// Register Chart.js components
Chart.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const props = defineProps({
  chartData: {
    type: Array,
    default: () => []
  },
  height: {
    type: Number,
    default: 200
  },
  type: {
    type: String,
    default: 'bar', // 'bar' or 'line'
    validator: (v) => ['bar', 'line'].includes(v)
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  showLimit: {
    type: Number,
    default: null
  }
})

const chartContainer = ref(null)
const chartCanvas = ref(null)
let chartInstance = null

// Create or update chart
function renderChart() {
  if (!chartCanvas.value || !props.chartData || props.chartData.length === 0) {
    return
  }

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  const ctx = chartCanvas.value.getContext('2d')

  // Prepare data
  const labels = props.chartData.map(item => formatLabel(item.periodStart))
  const data = props.chartData.map(item => item.totalPoints)

  // Create gradient
  const gradient = ctx.createLinearGradient(0, 0, 0, props.height)
  gradient.addColorStop(0, 'rgba(99, 102, 241, 0.4)')
  gradient.addColorStop(1, 'rgba(99, 102, 241, 0.05)')

  // Dataset configuration
  const datasets = [{
    label: '使用點數',
    data: data,
    backgroundColor: props.type === 'bar' ? 'rgba(99, 102, 241, 0.7)' : gradient,
    borderColor: 'rgb(99, 102, 241)',
    borderWidth: props.type === 'line' ? 2 : 0,
    borderRadius: props.type === 'bar' ? 4 : 0,
    fill: props.type === 'line',
    tension: 0.4,
    pointRadius: props.type === 'line' ? 4 : 0,
    pointBackgroundColor: 'rgb(99, 102, 241)',
    pointBorderColor: '#1a1a2e',
    pointBorderWidth: 2,
  }]

  // Add limit line if provided
  const annotations = {}
  if (props.showLimit) {
    annotations.limitLine = {
      type: 'line',
      yMin: props.showLimit,
      yMax: props.showLimit,
      borderColor: 'rgba(239, 68, 68, 0.7)',
      borderWidth: 2,
      borderDash: [6, 6],
      label: {
        display: true,
        content: `Limit: ${formatCompactNumber(props.showLimit)}`,
        position: 'end',
        backgroundColor: 'rgba(239, 68, 68, 0.8)',
        color: 'white',
        font: { size: 10 },
      }
    }
  }

  chartInstance = new Chart(ctx, {
    type: props.type,
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index',
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          backgroundColor: 'rgba(26, 26, 46, 0.95)',
          titleColor: '#fff',
          bodyColor: '#9ca3af',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          cornerRadius: 8,
          padding: 12,
          callbacks: {
            label: (context) => `${formatCompactNumber(context.raw)} points`,
          }
        },
      },
      scales: {
        x: {
          grid: {
            display: false,
          },
          ticks: {
            color: '#6b7280',
            font: { size: 11 },
          },
          border: {
            display: false,
          }
        },
        y: {
          grid: {
            color: 'rgba(255, 255, 255, 0.05)',
          },
          ticks: {
            color: '#6b7280',
            font: { size: 11 },
            callback: (value) => formatCompactNumber(value),
          },
          border: {
            display: false,
          },
          beginAtZero: true,
        }
      }
    }
  })
}

// Format date label
function formatLabel(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

// Watch for data changes
watch(
  () => props.chartData,
  () => {
    nextTick(() => renderChart())
  },
  { deep: true }
)

// Watch for type changes
watch(
  () => props.type,
  () => {
    nextTick(() => renderChart())
  }
)

onMounted(() => {
  nextTick(() => renderChart())
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})
</script>
