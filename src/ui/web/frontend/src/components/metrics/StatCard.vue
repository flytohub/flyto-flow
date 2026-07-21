<template>
  <div class="bg-gray-800 rounded-xl border border-gray-700 p-5">
    <!-- Loading State -->
    <template v-if="loading">
      <div class="animate-pulse">
        <div class="h-4 w-24 bg-gray-700 rounded mb-2"></div>
        <div class="h-8 w-20 bg-gray-600 rounded mb-2"></div>
        <div class="h-4 w-16 bg-gray-700 rounded"></div>
      </div>
    </template>

    <!-- Loaded State -->
    <template v-else>
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm text-gray-400">{{ title }}</span>
        <component
          :is="iconComponent"
          :size="20"
          :class="iconColorClass"
        />
      </div>

      <div class="flex items-baseline gap-1">
        <span class="text-2xl font-bold text-white">{{ value }}</span>
        <span v-if="suffix" class="text-lg text-gray-400">{{ suffix }}</span>
      </div>

      <div v-if="change !== undefined && change !== null" class="flex items-center gap-1 mt-1">
        <component
          :is="changeIcon"
          :size="14"
          :class="changeColorClass"
        />
        <span :class="changeColorClass" class="text-sm font-medium">
          {{ formatChange }}
        </span>
        <span class="text-xs text-gray-500">{{ $t('metrics.vsPrevious', 'vs previous') }}</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  BarChart3,
  CheckCircle,
  Clock,
  XCircle,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-vue-next'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  change: {
    type: Number,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  icon: {
    type: String,
    default: 'BarChart3'
  },
  color: {
    type: String,
    default: 'blue' // blue, green, purple, red
  },
  suffix: {
    type: String,
    default: ''
  },
  inverseChange: {
    type: Boolean,
    default: false // If true, negative change is good (e.g., for duration, failures)
  }
})

// Icon mapping
const iconMap = {
  BarChart3,
  CheckCircle,
  Clock,
  XCircle
}

const iconComponent = computed(() => iconMap[props.icon] || BarChart3)

// Icon color based on color prop
const iconColorClass = computed(() => {
  const colors = {
    blue: 'text-blue-400',
    green: 'text-green-400',
    purple: 'text-purple-400',
    red: 'text-red-400'
  }
  return colors[props.color] || colors.blue
})

// Change direction and icon
const isPositiveChange = computed(() => {
  if (props.change === 0) return null
  const positive = props.change > 0
  return props.inverseChange ? !positive : positive
})

const changeIcon = computed(() => {
  if (props.change === 0 || props.change === null) return Minus
  return props.change > 0 ? TrendingUp : TrendingDown
})

const changeColorClass = computed(() => {
  if (props.change === 0 || props.change === null) return 'text-gray-400'
  if (isPositiveChange.value) return 'text-green-400'
  return 'text-red-400'
})

const formatChange = computed(() => {
  if (props.change === null || props.change === undefined) return ''
  const sign = props.change > 0 ? '+' : ''
  return `${sign}${props.change.toFixed(1)}%`
})
</script>
