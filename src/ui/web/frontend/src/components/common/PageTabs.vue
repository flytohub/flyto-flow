<template>
  <div class="bg-gray-800/40 backdrop-blur-xl rounded-2xl border border-white/10 p-1.5 inline-flex items-center gap-1">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      @click="$emit('update:modelValue', tab.id)"
      :class="[
        'px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 flex items-center gap-2',
        modelValue === tab.id
          ? 'bg-gradient-to-r from-purple-600/30 to-pink-600/20 text-white border border-purple-500/30 shadow-lg shadow-purple-500/10'
          : 'text-gray-400 hover:text-white hover:bg-white/5'
      ]"
    >
      <component v-if="tab.icon" :is="tab.icon" :size="16" />
      {{ tab.label }}
      <span
        v-if="tab.count !== undefined"
        :class="[
          'px-1.5 py-0.5 rounded-full text-xs font-medium transition-colors',
          modelValue === tab.id
            ? 'bg-purple-500/30 text-purple-300'
            : 'bg-white/10 text-gray-500'
        ]"
      >
        {{ tab.count }}
      </span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    required: true
  },
  tabs: {
    type: Array,
    required: true
    // Each tab: { id: string, label: string, icon?: Component, count?: number }
  }
})

defineEmits(['update:modelValue'])
</script>

