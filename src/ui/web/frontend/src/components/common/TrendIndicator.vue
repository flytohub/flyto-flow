<template>
  <span
    :class="[
      'inline-flex items-center gap-1 text-sm font-medium',
      directionClasses
    ]"
  >
    <component
      :is="iconComponent"
      :size="14"
      :class="{ 'animate-pulse': isNeutral }"
    />
    <span>{{ formattedValue }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { TrendingUp, TrendingDown, Minus } from 'lucide-vue-next'

const props = defineProps({
  /**
   * Trend value (positive = up, negative = down, 0 = neutral)
   */
  value: {
    type: Number,
    required: true
  },
  /**
   * Show as percentage
   */
  isPercentage: {
    type: Boolean,
    default: true
  },
  /**
   * Invert colors (up = bad, down = good)
   */
  invertColors: {
    type: Boolean,
    default: false
  },
  /**
   * Show sign (+/-) prefix
   */
  showSign: {
    type: Boolean,
    default: true
  }
})

const isPositive = computed(() => props.value > 0)
const isNegative = computed(() => props.value < 0)
const isNeutral = computed(() => props.value === 0)

const directionClasses = computed(() => {
  if (isNeutral.value) {
    return 'text-gray-400'
  }

  const upColor = props.invertColors ? 'text-red-400' : 'text-green-400'
  const downColor = props.invertColors ? 'text-green-400' : 'text-red-400'

  return isPositive.value ? upColor : downColor
})

const iconComponent = computed(() => {
  if (isNeutral.value) return Minus
  return isPositive.value ? TrendingUp : TrendingDown
})

const formattedValue = computed(() => {
  const absValue = Math.abs(props.value)
  const formatted = props.isPercentage ? `${absValue}%` : absValue.toLocaleString()

  if (!props.showSign || isNeutral.value) {
    return formatted
  }

  return isPositive.value ? `+${formatted}` : `-${formatted}`
})
</script>
