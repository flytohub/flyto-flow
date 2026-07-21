<template>
  <div
    class="group relative bg-gray-800/40 hover:bg-gray-800/60 border border-gray-700/30 hover:border-purple-500/30 rounded-2xl overflow-hidden transition-all duration-500 hover:shadow-xl hover:shadow-purple-500/10"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
  >
    <!-- Glow Effect -->
    <div
      class="absolute inset-0 bg-gradient-to-br from-purple-500/10 via-transparent to-pink-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
    ></div>

    <!-- Content -->
    <div class="relative p-5">
      <!-- Header -->
      <div class="flex items-start gap-4 mb-4">
        <!-- Icon -->
        <div class="relative flex-shrink-0">
          <div
            :class="[
              'w-14 h-14 rounded-xl flex items-center justify-center transition-all duration-500',
              'bg-gradient-to-br',
              categoryGradient
            ]"
          >
            <component :is="categoryIcon" :size="24" class="text-white" />
          </div>
          <!-- Status Badge -->
          <div
            v-if="installed"
            class="absolute -bottom-1 -right-1 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center ring-2 ring-gray-800"
          >
            <Check :size="12" class="text-white" />
          </div>
        </div>

        <!-- Title & Author -->
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-white truncate group-hover:text-purple-300 transition-colors">
            {{ displayName }}
          </h3>
          <p class="text-sm text-gray-500 truncate">
            {{ plugin.author || 'Unknown' }}
          </p>
        </div>

        <!-- Downloads Badge -->
        <div
          v-if="plugin.downloads"
          class="flex items-center gap-1.5 px-2.5 py-1 bg-gray-700/50 rounded-full text-xs text-gray-400"
        >
          <Download :size="12" />
          <span>{{ formatCompactNumber(plugin.downloads) }}</span>
        </div>
      </div>

      <!-- Description -->
      <p class="text-sm text-gray-400 line-clamp-2 mb-4 min-h-[40px]">
        {{ plugin.description || $t('plugins.noDescription') }}
      </p>

      <!-- Tags -->
      <div class="flex flex-wrap gap-1.5 mb-4">
        <span
          v-for="tag in displayTags"
          :key="tag"
          class="px-2 py-0.5 bg-gray-700/50 rounded-md text-xs text-gray-400"
        >
          {{ tag }}
        </span>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-2">
        <template v-if="!installed">
          <button
            @click="$emit('install', plugin.model_id)"
            class="flex-1 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white text-sm font-medium rounded-xl transition-all duration-300 flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-purple-500/25 transform hover:scale-[1.02]"
          >
            <Download :size="16" />
            {{ $t('plugins.install') }}
          </button>
        </template>
        <template v-else>
          <button
            v-if="showStatus"
            @click="$emit('load', plugin.model_id)"
            class="flex-1 py-2.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 text-sm font-medium rounded-xl transition-all duration-300 flex items-center justify-center gap-2 border border-emerald-500/30"
          >
            <Play :size="16" />
            {{ $t('plugins.load') }}
          </button>
          <button
            @click="$emit('uninstall', plugin.model_id)"
            class="py-2.5 px-4 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-sm font-medium rounded-xl transition-all duration-300 flex items-center justify-center gap-2 border border-red-500/20 hover:border-red-500/30"
          >
            <Trash2 :size="16" />
          </button>
        </template>
      </div>
    </div>

    <!-- Hover Border Animation -->
    <div class="absolute inset-0 rounded-2xl pointer-events-none">
      <div
        class="absolute inset-0 rounded-2xl border-2 border-transparent"
        :class="{ 'animate-border-glow': isHovered }"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  Download, Check, Trash2, Play,
  MessageSquare, Image, Music, Cpu, Layers, Zap
} from 'lucide-vue-next'
import { formatCompactNumber } from '@/utils/format'

const props = defineProps({
  plugin: {
    type: Object,
    required: true
  },
  installed: {
    type: Boolean,
    default: false
  },
  showStatus: {
    type: Boolean,
    default: false
  }
})

defineEmits(['install', 'uninstall', 'load', 'unload'])

const isHovered = ref(false)

// Format display name
const displayName = computed(() => {
  const id = props.plugin.model_id || props.plugin.id || ''
  // Remove author prefix if present
  const parts = id.split('/')
  return parts.length > 1 ? parts[1] : id
})

// Get category from task or pipeline_tag
const category = computed(() => {
  const task = props.plugin.task || props.plugin.pipeline_tag || ''
  if (task.includes('text-generation') || task.includes('language')) return 'language'
  if (task.includes('embedding') || task.includes('feature')) return 'embedding'
  if (task.includes('image') || task.includes('vision')) return 'vision'
  if (task.includes('audio') || task.includes('speech')) return 'audio'
  return 'other'
})

// Category icon
const categoryIcon = computed(() => {
  const icons = {
    language: MessageSquare,
    embedding: Cpu,
    vision: Image,
    audio: Music,
    other: Layers
  }
  return icons[category.value] || Layers
})

// Category gradient
const categoryGradient = computed(() => {
  const gradients = {
    language: 'from-blue-500 to-cyan-500',
    embedding: 'from-purple-500 to-pink-500',
    vision: 'from-orange-500 to-red-500',
    audio: 'from-green-500 to-emerald-500',
    other: 'from-gray-500 to-gray-600'
  }
  return gradients[category.value] || gradients.other
})

// Display tags (limit to 3)
const displayTags = computed(() => {
  const tags = []
  if (props.plugin.task) tags.push(props.plugin.task)
  if (props.plugin.library_name) tags.push(props.plugin.library_name)
  if (props.plugin.pipeline_tag && props.plugin.pipeline_tag !== props.plugin.task) {
    tags.push(props.plugin.pipeline_tag)
  }
  return tags.slice(0, 3)
})

</script>

<style scoped>
@keyframes border-glow {
  0%, 100% {
    box-shadow: inset 0 0 0 1px rgba(168, 85, 247, 0);
  }
  50% {
    box-shadow: inset 0 0 0 1px rgba(168, 85, 247, 0.5);
  }
}

.animate-border-glow {
  animation: border-glow 2s ease-in-out infinite;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
