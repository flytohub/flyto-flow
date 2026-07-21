<template>
  <div
    class="feature-card group cursor-default transition-all duration-500
           relative p-6 rounded-2xl
           bg-white border border-gray-200
           dark:(bg-gray-800 border-gray-700)
           hover:(border-primary-300 shadow-xl shadow-primary-500/10 -translate-y-1)
           dark:hover:(border-primary-600 shadow-primary-500/5)"
  >
    <div
      class="feature-icon w-14 h-14 rounded-xl flex items-center justify-center text-white shadow-lg mb-5 group-hover:scale-110 transition-transform duration-300"
      :style="{ background: gradient }"
    >
      <component :is="icon" :size="28" :stroke-width="1.5" />
    </div>
    <h3 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-3">{{ title }}</h3>
    <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ description }}</p>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  icon: {
    type: [Object, Function],
    required: true
  },
  gradient: {
    type: String,
    default: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  }
})
</script>
