<template>
  <div v-if="availableTags.length" class="mt-4 mb-5 px-1">
    <div ref="containerRef" class="flex flex-wrap gap-2 overflow-hidden" :style="{ maxHeight: expanded ? 'none' : maxHeight }">
      <button
        v-for="tag in availableTags"
        :key="tag"
        @click="$emit('toggle-tag', tag)"
        class="tag-btn"
        :class="selectedTags.includes(tag)
          ? 'bg-purple-600/20 border-purple-500/50 text-purple-300 shadow-sm shadow-purple-500/10'
          : 'bg-gray-800/40 border-gray-700/50 text-gray-500 hover:border-gray-600 hover:text-gray-400 hover:bg-gray-800/60'"
      >
        <span class="flex items-center gap-1">
          <span v-if="selectedTags.includes(tag)" class="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
          #{{ tag }}
        </span>
      </button>
    </div>
    <div class="flex items-center gap-2 mt-2">
      <button
        v-if="hasOverflow && !expanded"
        @click="expanded = true"
        class="px-3 py-1 text-xs font-medium text-gray-500 hover:text-purple-400 bg-gray-800/40 border border-gray-700/50 hover:border-purple-500/30 rounded-lg transition-all duration-200"
      >
        +{{ hiddenCount }} more
      </button>
      <button
        v-if="expanded && hasOverflow"
        @click="expanded = false"
        class="px-3 py-1 text-xs text-gray-500 hover:text-gray-400 transition-colors duration-200"
      >
        Show less
      </button>
      <button
        v-if="selectedTags.length"
        @click="$emit('clear-tags')"
        aria-label="Clear tags"
        class="px-3 py-1 text-xs text-gray-600 hover:text-gray-400 transition-colors duration-200"
      >
        {{ $t('common.clearAll', 'Clear') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUpdated, nextTick } from 'vue'

const props = defineProps({
  availableTags: { type: Array, default: () => [] },
  selectedTags: { type: Array, default: () => [] },
})

defineEmits(['toggle-tag', 'clear-tags'])

const containerRef = ref(null)
const expanded = ref(false)
const hasOverflow = ref(false)
const hiddenCount = ref(0)

// 2 rows of tags: tag height ~32px + gap 8px = ~72px for 2 rows
const maxHeight = '72px'

function measureOverflow() {
  const el = containerRef.value
  if (!el) return

  // Temporarily expand to measure full height
  const prevMax = el.style.maxHeight
  el.style.maxHeight = 'none'
  const fullHeight = el.scrollHeight
  el.style.maxHeight = prevMax

  const twoRowHeight = 72
  hasOverflow.value = fullHeight > twoRowHeight

  if (hasOverflow.value) {
    // Count visible tags by checking which fit within 2 rows
    const children = el.children
    let visible = 0
    for (let i = 0; i < children.length; i++) {
      if (children[i].offsetTop < twoRowHeight) {
        visible++
      }
    }
    hiddenCount.value = props.availableTags.length - visible
  }
}

onMounted(() => nextTick(measureOverflow))
onUpdated(() => nextTick(measureOverflow))
</script>

<style scoped>
.tag-btn {
  @apply px-3 py-1.5 text-xs font-medium rounded-lg border transition-all duration-200;
}
</style>
