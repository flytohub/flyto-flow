<template>
  <div class="rounded-xl border border-white/5 overflow-hidden">
    <!-- Section Toggle Header -->
    <button
      @click="toggle"
      class="w-full flex items-center justify-between px-4 py-3 bg-gray-800/40 hover:bg-gray-800/60 transition-colors"
    >
      <span :class="['text-sm font-medium', colorClasses.text]">{{ label }}</span>
      <ChevronDown
        :size="16"
        :class="['text-gray-400 transition-transform duration-300', { 'rotate-180': !isOpen }]"
      />
    </button>

    <!-- Collapsible Content -->
    <div
      ref="contentRef"
      class="transition-all duration-300 ease-in-out overflow-hidden"
      :style="contentStyle"
    >
      <div ref="innerRef" class="px-4 py-3">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

const props = defineProps({
  label: { type: String, required: true },
  color: {
    type: String,
    default: 'gray',
    validator: (v) => ['emerald', 'red', 'amber', 'gray'].includes(v),
  },
  defaultOpen: { type: Boolean, default: true },
})

const isOpen = ref(props.defaultOpen)
const contentRef = ref(null)
const innerRef = ref(null)
const contentHeight = ref(0)

const COLOR_MAP = {
  emerald: { text: 'text-emerald-400' },
  red: { text: 'text-red-400' },
  amber: { text: 'text-amber-400' },
  gray: { text: 'text-gray-400' },
}

const colorClasses = computed(() => COLOR_MAP[props.color] || COLOR_MAP.gray)

const contentStyle = computed(() => {
  if (isOpen.value) {
    return { maxHeight: contentHeight.value ? `${contentHeight.value}px` : 'none' }
  }
  return { maxHeight: '0px' }
})

function measureHeight() {
  if (innerRef.value) {
    contentHeight.value = innerRef.value.scrollHeight + 24 // py-3 top + bottom = 24px
  }
}

function toggle() {
  if (!isOpen.value) {
    measureHeight()
  }
  isOpen.value = !isOpen.value
}

onMounted(() => {
  nextTick(measureHeight)
})

// Re-measure when slot content might have changed
watch(() => props.label, () => {
  nextTick(measureHeight)
})
</script>
