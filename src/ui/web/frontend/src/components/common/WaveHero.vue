<template>
  <section :class="['relative overflow-hidden', gradientClass]">
    <!-- Animated grid background -->
    <div class="absolute inset-0 opacity-20">
      <div
        class="absolute inset-0"
        :style="gridStyle"
      ></div>
    </div>

    <!-- Floating orbs -->
    <div :class="['absolute w-72 h-72 rounded-full blur-3xl animate-pulse', orb1Class, orb1Position]"></div>
    <div
      :class="['absolute w-96 h-96 rounded-full blur-3xl animate-pulse', orb2Class, orb2Position]"
      style="animation-delay: 1s;"
    ></div>

    <!-- Content -->
    <div :class="['container relative z-10 px-4', paddingClass]">
      <slot></slot>
    </div>

    <!-- Wave divider -->
    <div class="absolute bottom-0 left-0 w-full">
      <svg
        class="relative block w-full"
        :style="{ height: waveHeight }"
        viewBox="0 0 1440 60"
        preserveAspectRatio="none"
      >
        <path
          d="M0,30 C360,60 720,0 1080,30 C1260,45 1380,30 1440,30 L1440,60 L0,60 Z"
          class="fill-gray-50 dark:fill-gray-900"
        ></path>
      </svg>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: {
    type: String,
    default: 'medium',
    validator: (v) => ['small', 'medium', 'large'].includes(v)
  },
  variant: {
    type: String,
    default: 'purple',
    validator: (v) => ['purple', 'indigo', 'blue'].includes(v)
  },
  gridSize: {
    type: Number,
    default: 50
  },
  waveHeight: {
    type: String,
    default: '40px'
  }
})

const paddingClass = computed(() => {
  const sizes = {
    small: 'py-8 sm:py-10',
    medium: 'py-10 sm:py-12',
    large: 'py-12 lg:py-16'
  }
  return sizes[props.size] || sizes.medium
})

const gradientClass = computed(() => {
  const variants = {
    purple: 'bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900',
    indigo: 'bg-gradient-to-br from-gray-900 via-indigo-900 to-gray-900',
    blue: 'bg-gradient-to-br from-indigo-900 via-purple-900 to-indigo-900'
  }
  return variants[props.variant] || variants.purple
})

const gridColorMap = {
  purple: 'rgba(139, 92, 246, 0.3)',
  indigo: 'rgba(99, 102, 241, 0.3)',
  blue: 'rgba(139, 92, 246, 0.3)'
}

const gridStyle = computed(() => ({
  backgroundImage: `linear-gradient(${gridColorMap[props.variant]} 1px, transparent 1px), linear-gradient(90deg, ${gridColorMap[props.variant]} 1px, transparent 1px)`,
  backgroundSize: `${props.gridSize}px ${props.gridSize}px`
}))

const orb1Class = computed(() => {
  const variants = {
    purple: 'bg-purple-500/20',
    indigo: 'bg-indigo-500/20',
    blue: 'bg-purple-500/20'
  }
  return variants[props.variant] || variants.purple
})

const orb2Class = computed(() => {
  const variants = {
    purple: 'bg-blue-500/20',
    indigo: 'bg-purple-500/20',
    blue: 'bg-blue-500/20'
  }
  return variants[props.variant] || variants.purple
})

const orb1Position = computed(() => {
  const variants = {
    purple: 'top-20 left-10',
    indigo: 'top-10 right-20',
    blue: 'top-10 left-20'
  }
  return variants[props.variant] || variants.purple
})

const orb2Position = computed(() => {
  const variants = {
    purple: 'bottom-10 right-10',
    indigo: 'bottom-10 left-10',
    blue: 'bottom-10 right-20'
  }
  return variants[props.variant] || variants.purple
})
</script>
